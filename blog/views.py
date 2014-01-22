from framework import app

from flask import Blueprint
from flask import render_template

from flask import flash, redirect
from forms import LoginForm

blog_blueprint = Blueprint('blog', __name__, url_prefix='/blog',  template_folder='templates')

@blog_blueprint.route('/')
@blog_blueprint.route('/index')
def index():
    user = { 'nickname': 'Miguel' } # fake user
    posts = [ # fake array of posts
        { 
            'author': { 'nickname': 'John' }, 
            'body': 'Beautiful day in Portland!' 
        },
        { 
            'author': { 'nickname': 'Susan' }, 
            'body': 'The Avengers movie was so cool!' 
        }
    ]
    return render_template("index.html",
        title = 'Home',
        user = user,
        posts = posts)


@blog_blueprint.route('/login', methods = ['GET', 'POST'])
def login():
    form = LoginForm()
    return render_template('login.html', 
        title = 'Sign In',
        form = form)
