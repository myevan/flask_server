import os

from flask import Flask
from environments import Environments
from database import SQLAlchemy

app = Flask(__name__)
env = Environments(app, os.path.dirname(os.path.realpath(__file__)))
db = SQLAlchemy(app)
