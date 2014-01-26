import os

from flask import Flask
from flask.ext.login import LoginManager
from flask.ext.openid import OpenID
from environments import Environments
from database import SQLAlchemy

app = Flask(__name__)
env = Environments(app, os.path.dirname(os.path.realpath(__file__)))
db = SQLAlchemy(app)
oid = OpenID(app, env.temp_dir_path)
lm = LoginManager()
lm.init_app(app)

