import logging
import os
from functools import wraps
from uuid import uuid4

import magic
from colorama import Fore, Style, init
from flask import (Flask, redirect, render_template, request,
                   send_from_directory, session)
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from PIL import Image

import config
import db
from flask_session import Session

app = Flask(__name__)
app.config.from_pyfile('config.py')
app.secret_key = config.SECRET_KEY
Session(app)
CORS(app)

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


def login_required(func):
    @wraps(func)
    def login_wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return redirect('/login')
        return func(*args, **kwargs)
    return login_wrapper


def check_request(req):
    if 'file' not in req.files:
        return [False, 400, 'No file uploaded\n']
    file = req.files['file']

    if file.filename == '':
        return [False, 400, 'Empty file name\n']

    if not ('.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in
            {'png', 'jpg', 'jpeg', 'gif', 'bmp'}):
        return [False, 415, 'File extension not allowed\n']

    if not magic.from_buffer(file.read(), mime=True).startswith('image/'):
        return [False, 400,  'Invalid image file\n']
    file.seek(0)
    return [True, file]


@app.errorhandler(413)
def request_entity_too_large(_):
    if request.args.get('s'):
        return render_template('index.html', error=[413, "File size too large"]), 413
    return "File size too large\n", 413


@app.errorhandler(429)
def too_many_requests(_):
    if request.args.get('s'):
        return render_template('index.html', error=[429, "Too many requests"]), 429
    return "Too many requests\n", 429


@app.errorhandler(404)
def page_not_found(_):
    return render_template('404.html', error="page not found"), 404


@app.route('/')
@login_required
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        if 'user_id' in session:
            return redirect('/')
        return render_template('login.html')
    username = request.form.get('username')
    password = request.form.get('password')

    user = db.login(username, password)

    if user:
        session.permanent = True
        session['user_id'] = user.user_id
        return redirect('/')
    else:
        return render_template('login.html', error=[401, "Invalid username or password"])


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        if 'user_id' in session:
            return redirect('/')
        return render_template('register.html')
    username = request.form.get('username')
    password = request.form.get('password')

    if db.session.query(db.User).filter_by(username=username).first():
        return render_template('register.html', error=[400, "Username already exists"])

    db.register(username, password, user_id=uuid4().hex)
    user = db.login(username, password)

    if user:
        session.permanent = True
        session['user_id'] = user.user_id
        return redirect('/')


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


@app.route('/mine')
@login_required
def mine():
    images = db.get_images(session['user_id'])
    print(images)
    return render_template('mine.html', images=images)


@app.route('/upload', methods=['POST'])
@limiter.limit(app.config['RATE_LIMIT'], override_defaults=False)
@login_required
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
        asp = image.width / image.height
        new_width = 3840 if image.width > image.height else int(2160 * asp)
        new_height = int(new_width / asp)

        image = image.resize((new_width, new_height), Image.LANCZOS)

    image_id = uuid4().hex
    save_path = os.path.join(app.config['UPLOAD_FOLDER'], image_id + '.jpg')

    image.save(save_path, 'JPEG', quality=75)
    logger.info(f"{Fore.GREEN}Image uploaded: {image_id}{Style.RESET_ALL}")
    db.add_image(image_id, session['user_id'])
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


@app.route('/d/<image_id>')
@login_required
def delete(image_id):
    success = db.delete_image(image_id, session['user_id'])
    if success:
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_id + '.jpg')
        if os.path.exists(image_path):
            os.remove(image_path)
        return redirect('/mine')
    else:
        return render_template('404.html', error="image not found"), 404


if __name__ == '__main__':
    app.run(host='localhost', port=8081, threaded=True)
