# Web Image Scraper

This Python script allows you to scrape images from a webpage using ScrapingBee's API. It downloads images that meet a specified minimum size requirement, making it useful for collecting high-quality images from websites.

## Features

- Scrapes images from any specified webpage
- Uses ScrapingBee's API for efficient and reliable scraping
- Downloads only images that meet a minimum size requirement
- Handles various image formats including JPEG, PNG, GIF, WebP, and HEIF/HEIC
- Configurable output directory and minimum image size
- Command-line interface for easy use

## Prerequisites

Before you begin, ensure you have met the following requirements:

- Docker installed on your system
- ScrapingBee API key

## Installation

1. Clone this repository or download the script files.

2. Create a `.env` file in the project root and add your ScrapingBee API key:
   ```
   SCRAPINGBEE_API_KEY=your_api_key_here
   ```

3. Build the Docker image:
   ```
   sudo docker build -t web-image-scraper .
   ```

## Usage

First, run the Docker container and access its bash shell:

```
sudo docker run -it --rm -v $(pwd):/app -v $(pwd)/images:/app/images web-image-scraper bash
```

This command does the following:
- `-it`: Runs the container interactively
- `--rm`: Removes the container when it exits
- `-v $(pwd):/app`: Mounts the current directory to /app in the container
- `-v $(pwd)/images:/app/images`: Mounts the images directory
- `web-image-scraper`: The name of our Docker image
- `bash`: Runs the bash shell in the container

Once you're inside the container's bash shell, you can run the script using:

```
python main.py <url> [options]
```

### Arguments:

- `url`: The webpage URL to scrape (required)

### Options:

- `-o, --output`: Specify the output folder for downloaded images (default: "scraped_images")
- `-m, --min-area`: Specify the minimum image area in pixels (default: 50000)
- `-h, --help`: Show the help message and exit

### Example:

While inside the Docker container's bash shell:

```
python main.py https://www.ai21.com/blog/the-promise-of-rag-bringing-enterprise-generative-ai-to-life -o /app/images -m 50000
```

This will scrape images from the specified URL, save them to the `/app/images` directory (which is mounted to your host machine), and only keep images with an area of at least 50,000 pixels.

To exit the Docker container after you're done, simply type:

```
exit
```

This will return you to your host machine's shell.

## How It Works

1. The script uses ScrapingBee's API to fetch the HTML content of the specified URL.
2. It extracts all `<img>` elements from the HTML.
3. For each image found, it:
   - Attempts to download the image
   - Checks the image dimensions
   - If the image meets the minimum size requirement, it saves the image to the specified output folder
   - Skips images that are too small or fail to download

## Project Structure

- `main.py`: The main script that handles image scraping and downloading
- `requirements.txt`: List of Python dependencies
- `Dockerfile`: Instructions for building the Docker image
- `.env`: Contains the ScrapingBee API key (not included in the repository)

## WEBPAGE TESTS

### FOR AVIF and SVG
```
python main.py https://www.ai21.com/blog/the-promise-of-rag-bringing-enterprise-generative-ai-to-life -o /app/images -m 50000
```

### FOR PNG and WEBP
```
python main.py https://blog.tinify.com/pros-and-cons-webp-images/ -o /app/images -m 50000
```

## Contributing

Contributions to this project are welcome. Please fork the repository and submit a pull request with your changes.

## License

This project is open source and available under the [MIT License](LICENSE).

## Disclaimer

Web scraping may be against the terms of service of some websites. Ensure you have permission or the right to scrape the target website before using this script. Use responsibly and respect website owners' rights and server resources. Be aware of ScrapingBee's terms of service and any limitations on their API usage.