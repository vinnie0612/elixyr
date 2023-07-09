import logging
import os
from uuid import uuid4

import magic
from functools import wraps
from colorama import Fore, Style, init
from flask import (Flask, redirect, render_template, request,
                   send_from_directory)
from flask_cors import CORS
from PIL import Image
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

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

# Initialize Flask-Limiter
limiter = Limiter(
    get_remote_address,
    app=app,
    storage_uri="memory://",
)

def check_request(request):
    if 'file' not in request.files:
        return [False, 400, 'No file uploaded\n'] 
    file = request.files['file']

    if file.filename == '':
        return [False, 400, 'Empty file name\n']

    if not ('.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif', 'bmp'}):
        return [False, 415, 'File extension not allowed\n']

    if not magic.from_buffer(file.read(), mime=True).startswith('image/'):
        return [False, 400,  'Invalid image file\n']
    file.seek(0)
    return [True, file]

@app.errorhandler(413)
def request_entity_too_large():
    if request.args.get('s'):
        return render_template('index.html', error=[413, "File size too large"]), 413
    return "File size too large\n", 413

@app.errorhandler(429)
def too_many_requests(*args, **kwargs):
    if request.args.get('s'):
        return render_template('index.html', error=[429, "Too many requests"]), 429
    return "Too many requests\n", 429

@app.errorhandler(404)
def page_not_found():
    return render_template('404.html', error="page not found"), 404

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
@limiter.limit("40/minute", override_defaults=False)
def upload():
    check = check_request(request)
    if not check[0]:
        logger.error(f"{Fore.RED}Upload failed: {check[2]}{Style.RESET_ALL}")
        if request.args.get('s'):
            return render_template('index.html', error=check[1:]), check[1]
        return check[2], check[1]
    file = check[1]

    image = Image.open(file)
    image = image.convert('RGB')

    # Resize image below 4K and compress
    if image.width > 3840 or image.height > 2160:
        aspect_ratio = image.width / image.height
        new_width = 3840 if image.width > image.height else int(2160 * aspect_ratio)
        new_height = int(new_width / aspect_ratio)
        
        image = image.resize((new_width, new_height), Image.LANCZOS)

    image_id = uuid4().hex
    save_path = os.path.join(app.config['UPLOAD_FOLDER'], image_id + '.jpg')

    image.save(save_path, 'JPEG', quality=75)
    logger.info(f"{Fore.GREEN}Image uploaded: {image_id}{Style.RESET_ALL}")
    if request.args.get('s'):
        return redirect(f'/i/{image_id}')
    else:
        return f'{image_id}\n', 200

@app.route('/i/<image_id>')
def image(image_id):
    image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_id + '.jpg')
    if not os.path.exists(image_path):
        logger.error(f"{Fore.RED}Image not found: {image_id}{Style.RESET_ALL}")  # Log image not found
        return render_template('404.html', error="image not found"), 404
    else:
        return send_from_directory(app.config['UPLOAD_FOLDER'], image_id + '.jpg')

if __name__ == '__main__':
    app.run(host='localhost', port=8081, threaded=True)
