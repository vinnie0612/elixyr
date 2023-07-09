from flask import Flask, render_template, request, send_from_directory
from flask_cors import CORS
from PIL import Image
from uuid import uuid4
import logging
import os
from colorama import init, Fore, Style

app = Flask(__name__)
CORS(app)
app.config.from_pyfile('config.py')

# Initialize colorama
init(autoreset=True)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.setLevel(logging.ERROR)


def check_request(request):
    if 'file' not in request.files:
        return [False, 400, 'No file uploaded'] 
    file = request.files['file']

    if file.filename == '':
        return [False, 400, 'Empty file name']

    if not ('.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}):
        return [False, 403, 'File extension not allowed']

    return [True, file]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    check = check_request(request)
    if not check[0]:
        logger.error(f"{Fore.RED}Upload failed: {check[2]}{Style.RESET_ALL}")  # Log error message
        return check[1], check[2]
    file = check[1]
    image = Image.open(file)
    image = image.convert('RGB')

    # Check if the image is above 3840x2160 pixels
    if image.width > 3840 or image.height > 2160:
        # Calculate the new dimensions while preserving aspect ratio
        aspect_ratio = image.width / image.height
        new_width = 3840 if image.width > image.height else int(2160 * aspect_ratio)
        new_height = int(new_width / aspect_ratio)
        
        # Resize the image
        image = image.resize((new_width, new_height), Image.LANCZOS)

    image_id = uuid4().hex
    save_path = os.path.join(app.config['UPLOAD_FOLDER'], image_id + '.jpg')

    image.save(save_path, 'JPEG', quality=75)
    logger.info(f"{Fore.GREEN}Image uploaded: {image_id}{Style.RESET_ALL}")  # Log image upload

    return f'{image_id}\n', 200

@app.route('/<image_id>')
def image(image_id):
    image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_id + '.jpg')
    if not os.path.exists(image_path):
        logger.error(f"{Fore.RED}Image not found: {image_id}{Style.RESET_ALL}")  # Log image not found
        return 'Image not found', 404
    else:
        return send_from_directory(app.config['UPLOAD_FOLDER'], image_id + '.jpg')

if __name__ == '__main__':
    app.run(host='localhost', port=8081, threaded=True)