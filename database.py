from flask import *
from flask_sqlalchemy import SQLAlchemy

# configuration
DATABASE = '/tmp/babylone.db'
DEBUG = True
SECRET_KEY = 'development key'
UPLOAD_FOLDER = './static/image_flask'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

# create our little application :)
app = Flask(__name__)
app.config.from_object(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/babylone.db'
db = SQLAlchemy(app)
