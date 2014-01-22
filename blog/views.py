from framework import app

from flask import Blueprint
from flask import render_template


blog_blueprint = Blueprint('blog', __name__, url_prefix='/blog')

@blog_blueprint.route('/')
@blog_blueprint.route('/index')
def index():
    user = { 'nickname': 'Miguel' } # fake user
    return '''
<html>
  <head>
    <title>Home Page</title>
  </head>
  <body>
    <h1>Hello, ''' + user['nickname'] + '''</h1>
  </body>
</html>
'''
