# Elixyr

Elixyr is a web application developed using the Flask framework that allows users to upload, resize, and compress images. It provides a simple and intuitive interface for image uploading, while also allowing users to upload files using its "API".

## Features

- Image upload: Users can upload images in formats such as PNG, JPG, JPEG, GIF, and BMP.
- Image resizing: Uploaded images are automatically resized to a maximum of 4K and compressed.
- Unique image IDs: Each uploaded image is assigned a unique ID for easy access and retrieval.

## Prerequisites

- Docker
- Preferrably a reverse proxy (e.g nginx)

## Usage

### Uploading Images

You can upload images to Elixyr using the command-line interface (CLI) by sending a POST request to the `/upload` endpoint. Follow the example below:

```shell
curl -X POST -F "file=@image.jpg" https://elixyr.tld/upload
```

Replace `image.jpg` with the path to your image file. The server will respond with a unique `example_id` representing your uploaded image.

### Accessing Uploaded Images

Once you have uploaded an image, you can access it using the following URL format:

```uri
https://elixyr.tld/i/example_id
```

Replace `example_id` with the unique ID provided in the response when you uploaded the image. This URL will display the uploaded image in your web browser.

Accepted File Extensions: 'png', 'jpg', 'jpeg', 'gif', 'bmp'

## Getting Started

1. Clone the repository:

   ```shell
   git clone https://github.com/your-username/elixyr.git
   cd elixyr
   ```

2. Review config.py and docker-compose.yml

    Please review these files for any changes you might want to make.

3. Run it with docker

    ```shell
    docker-compose up -d
    ```

## Configuration

The application can be configured by modifying the settings in the `config.py` file. The available configuration options include:

- `UPLOAD_FOLDER`: The directory where uploaded images will be stored.
- `RATE_LIMIT`: The maximum number of image uploads allowed per minute.
- `MAX_CONTENT_LENGTH`: The maximum file size

## Error Handling

The application provides error handling for basic errors with a pretty error page.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more information
