from framework import app

from flask import Blueprint
from flask import render_template


blog_blueprint = Blueprint('blog', __name__, url_prefix='/blog',  template_folder='templates')

@blog_blueprint.route('/')
@blog_blueprint.route('/index')
def index():
    user = { 'nickname': 'Miguel' } # fake user
    return render_template("index.html",
        title = 'Home',
        user = user)
