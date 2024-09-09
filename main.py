import os
import json
import hashlib
import argparse
from dotenv import load_dotenv
from scrapingbee import ScrapingBeeClient
import requests
from io import BytesIO
from urllib.parse import urljoin
from PIL import Image, UnidentifiedImageError
import pillow_heif
import pyjxl
from pathlib import Path
from xml.etree import ElementTree as ET

pillow_heif.register_heif_opener()

try:
    import pillow_avif

    Image.register_open(
        pillow_avif.AvifImagePlugin.AvifImageFile.format,
        pillow_avif.AvifImagePlugin.AvifImageFile,
    )
except ImportError:
    pass

# Load environment variables
load_dotenv()


def md5_hash(url):
    return hashlib.md5(url.encode("utf-8")).hexdigest()


def get_api_key():
    api_key = os.getenv("SCRAPINGBEE_API_KEY")
    if not api_key:
        raise ValueError("SCRAPINGBEE_API_KEY not found in .env file")
    return api_key


# SVG size function to extract width and height from SVG content
def get_svg_size(content):
    try:
        root = ET.fromstring(content)
        width = root.attrib.get("width", "0")
        height = root.attrib.get("height", "0")

        # Convert width and height to float, handling various units
        width = float(
            width.replace("px", "").replace("em", "").replace("%", "").strip() or "0"
        )
        height = float(
            height.replace("px", "").replace("em", "").replace("%", "").strip() or "0"
        )

        return (width, height) if width and height else (0, 0)
    except Exception as e:
        print(f"Error getting SVG size: {str(e)}")
    return 0, 0


# handler for SVG files
def handle_svg(url, response_content, folder, min_area):
    try:
        width, height = get_svg_size(response_content)
        if width * height >= min_area:
            img_hash = md5_hash(url)
            extension = "svg"
            filename = os.path.join(folder, f"{img_hash}.{extension}")

            # Save SVG file
            with open(filename, "wb") as f:
                f.write(response_content)
            print(f"Downloaded: {filename} (Size: {width}x{height}, Format: SVG)")

            # Save metadata
            metadata = {"url": url, "format": "SVG", "size": (width, height)}
            metadata_filename = os.path.join(folder, f"{img_hash}.json")
            with open(metadata_filename, "w") as f:
                json.dump(metadata, f, indent=2)
            print(f"Metadata saved: {metadata_filename}")
        else:
            print(f"Skipped (too small): {url} (Size: {width}x{height}, Format: SVG)")
    except Exception as e:
        print(f"Error handling SVG image {url}: {str(e)}")


# handler for JPEG XL files
def handle_jpeg_xl(url, response_content, folder):
    try:
        img_hash = md5_hash(url)
        extension = "jxl"
        filename = os.path.join(folder, f"{img_hash}.{extension}")

        # Save JPEG XL image to file
        with open(filename, "wb") as f:
            f.write(response_content)

        # Decode the JPEG XL image using pyjxl
        image = pyjxl.decode(BytesIO(response_content))
        width, height = image.size
        print(f"Downloaded: {filename} (Size: {width}x{height}, Format: JPEG XL)")

        # Save metadata
        metadata = {"url": url, "format": "JPEG XL", "size": (width, height)}
        metadata_filename = os.path.join(folder, f"{img_hash}.json")
        with open(metadata_filename, "w") as f:
            json.dump(metadata, f, indent=2)
        print(f"Metadata saved: {metadata_filename}")

    except Exception as e:
        print(f"Error handling JPEG XL image {url}: {str(e)}")


# handler for other images (PNG, JPEG, Webp, HEIF/HEIC, etc.) using PIL
def handle_generic_image(url, response_content, folder, min_area):
    try:
        with Image.open(BytesIO(response_content)) as img:
            width, height = img.size
            if width * height >= min_area:
                img_hash = md5_hash(url)
                extension = img.format.lower()
                filename = os.path.join(folder, f"{img_hash}.{extension}")

                # Save the image
                with open(filename, "wb") as f:
                    f.write(response_content)
                print(
                    f"Downloaded: {filename} (Size: {width}x{height}, Format: {img.format})"
                )

                # Save metadata
                metadata = {"url": url, "format": img.format, "size": (width, height)}
                metadata_filename = os.path.join(folder, f"{img_hash}.json")
                with open(metadata_filename, "w") as f:
                    json.dump(metadata, f, indent=2)
                print(f"Metadata saved: {metadata_filename}")
            else:
                print(
                    f"Skipped (too small): {url} (Size: {width}x{height}, Format: {img.format})"
                )
    except UnidentifiedImageError:
        print(f"Image format not recognized for {url}")
    except Exception as e:
        print(f"Error handling image {url}: {str(e)}")


# Centralized function to call the appropriate handler based on the content-type
def download_image(url, folder, min_area):
    try:
        # Perform a single request
        response = requests.get(url)
        if response.status_code == 200:
            content_type = response.headers.get("Content-Type", "")
            if "image/svg+xml" in content_type:
                handle_svg(url, response.content, folder, min_area)
            elif "image/jxl" in content_type:
                handle_jpeg_xl(url, response.content, folder)
            else:
                handle_generic_image(url, response.content, folder, min_area)
        else:
            print(f"Failed to download: {url}, Status code: {response.status_code}")
    except Exception as e:
        print(f"Error downloading {url}: {str(e)}")


# Scrape images from a webpage
def scrape_images(url, output_folder, min_area):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    api_key = get_api_key()
    client = ScrapingBeeClient(api_key=api_key)

    params = {
        "render_js": True,
        "extract_rules": {
            "all_images": {
                "selector": "img",
                "type": "list",
                "output": {
                    "src": {"selector": "img", "output": "@src"},
                    "data-src": {"selector": "img", "output": "@data-src"},
                },
            }
        },
    }

    try:
        print("Sending request to ScrapingBee...")
        response = client.get(url, params=params)
        print(f"Response received. Status code: {response.status_code}")

        if response.ok:
            data = json.loads(response.content)
            print(f"Extracted data: {json.dumps(data, indent=2)}")

            img_urls = []
            for img in data.get("all_images", []):
                src = img.get("src") or img.get("data-src")
                if src:
                    full_url = urljoin(url, src)
                    # Check if the URL is valid
                    if not full_url.startswith("http"):
                        print(f"Invalid URL skipped: {full_url}")
                        continue
                    img_urls.append(full_url)

            print(f"Found {len(img_urls)} valid image URLs")

            for img_url in img_urls:
                try:
                    # Check URL validity by making a HEAD request
                    head_response = requests.head(img_url)
                    if (
                        head_response.status_code == 200
                        and "image" in head_response.headers.get("Content-Type", "")
                    ):
                        print(f"Processing image: {img_url}")
                        download_image(img_url, output_folder, min_area)
                    else:
                        print(f"Skipped (not an image or not accessible): {img_url}")
                except Exception as e:
                    print(f"Error validating image URL {img_url}: {str(e)}")

        else:
            print(f"Failed to scrape the website. Status code: {response.status_code}")
            print(f"Response: {response.text}")

    except Exception as e:
        print(f"Error during scraping: {str(e)}")


# Main function with argument parsing
def main():
    parser = argparse.ArgumentParser(
        description="Scrape images from a webpage using ScrapingBee."
    )
    parser.add_argument("url", help="URL of the webpage to scrape")
    parser.add_argument(
        "-o",
        "--output",
        default="scraped_images",
        help="Output folder for downloaded images",
    )
    parser.add_argument(
        "-m", "--min-area", type=int, default=50000, help="Minimum image area in pixels"
    )

    args = parser.parse_args()

    print(f"Scraping images from: {args.url}")
    print(f"Saving to: {args.output}")
    print(f"Minimum image area: {args.min_area} pixels")

    scrape_images(args.url, args.output, args.min_area)


if __name__ == "__main__":
    main()
