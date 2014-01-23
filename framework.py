import os

from flask import Flask
from flask.ext.login import LoginManager
from flask.ext.openid import OpenID
from environments import Environments
from database import SQLAlchemy

base_dir_path = os.path.dirname(os.path.realpath(__file__))
app = Flask(__name__)
env = Environments(app, base_dir_path)
db = SQLAlchemy(app)
oid = OpenID(app, os.path.join(base_dir_path, 'temp'))
lm = LoginManager()
lm.init_app(app)
