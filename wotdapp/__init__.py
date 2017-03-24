import os, random
import re
from datetime import datetime
from functools import wraps
from flask import Flask, request, render_template, redirect, url_for, flash, abort, make_response, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_assets import Environment, Bundle
import flask_login
from flask_bcrypt import Bcrypt
from flask_sslify import SSLify
import requests

app = Flask(__name__, instance_relative_config=True)

## Load external configuration
#################################################

app.config.from_object('config')
try:
    app.config.from_pyfile('instanceconfig.py')
except IOError:
    pass

## Force SSL (where debug=False)
#################################################

sslify = SSLify(app)


## Process SCSS, bundle CSS and JS
#################################################

env = Environment(app)

env.load_path = [
    os.path.join(os.path.dirname(__file__), 'sass'),
    os.path.join(os.path.dirname(__file__), 'bower_components'),
]

env.register(
    'css_all',
    Bundle(
        os.path.join('bootstrap', 'dist', 'css', 'bootstrap.min.css.map'),
        os.path.join('bootstrap', 'dist', 'css', 'bootstrap.min.css'),
        Bundle('custom.scss', filters='scss', output='css_all.css'),
    )
)

env.register(
    'js_all',
    Bundle(
        os.path.join('jquery', 'dist', 'jquery.min.js'),
        os.path.join('bootstrap', 'dist', 'js', 'bootstrap.min.js'),
    )
)

## database things
#################################################

# #old plans?
# @app.teardown_appcontext
# def shutdown_session(exception=None):
#     db_session.remove()

# new plans?
db = SQLAlchemy(app)
migrate = Migrate(app, db)


## authentication things
#################################################

login_manager = flask_login.LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message = u"You'll need to login to access that page."
login_manager.login_message_category = "info"

@login_manager.user_loader
def user_loader(user_id):
    return User.query.get(user_id)

bcrypt = Bcrypt(app)


def requires_mod(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not flask_login.current_user.isMod:
            return abort(403)
        return f(*args, **kwargs)
    return wrapped


## General Routes
#################################################

# import models here so models.py can import the app's bcrypt instance
from models import User, Post

@app.route("/")
def index():
    # TODO limit to recent posts so that this is better in scale...
    count = Post.query.count()
    try:
        win = session.pop('NewPostContent')
    except:
        win = None

    if win is None:
        posts = Post.query.filter_by(isApproved=True).all()
        if len(posts) is 0:
            win = 'Today, I wrote a post to populate this when something goes wrong.'
        else:
            p = random.choice(posts)
            win = p.content
    return render_template('home.html', win=win, count=count)

@app.route("/submit", methods=['GET', 'POST'])
def submit():
    if request.method == 'GET':
        return render_template('submit.html', captcha=app.config['REQUIRE_CAPTCHA'])
    elif request.method == 'POST':
        post_content = request.form.get("content")
        if app.config['REQUIRE_CAPTCHA']:
            captcha_data = {
                'secret': app.config['RECAPTCHA_SECRET'],
                'response': request.form.get("g-recaptcha-response")
            }
            verify = requests.post(
                'https://www.google.com/recaptcha/api/siteverify',
                data=captcha_data)
        if (not app.config['REQUIRE_CAPTCHA']) or verify.json()['success']:
            try:
                uid = flask_login.current_user.id
            except:
                uid = None
            p = Post(post_content, uid)
            db.session.add(p)
            db.session.commit()
            flash('Awesome! Keep up the good work!', 'success')
            session['NewPostContent'] = post_content
            return redirect(url_for('index'))
        return redirect(url_for('index'))

@app.route("/me")
@flask_login.login_required
def user_home():
    user_posts = Post.query.filter_by(user_id=flask_login.current_user.id) \
        .order_by(Post.create_time.desc()).all()
    user_name = flask_login.current_user.getName()
    return render_template('user.html', name=user_name, posts=user_posts)

@app.route("/me", methods=['POST'])
@flask_login.login_required
def user_settings():
    u = User.query.get(flask_login.current_user.id)
    u.name = request.form.get("displayname")
    u.email = request.form.get("email")
    db.session.add(u)
    db.session.commit()
    flash('Settings Updated', 'info')
    return redirect(url_for('user_home'))




## Authentication Routes
#################################################

@app.route("/join", methods=['GET', 'POST'])
def join():
    if request.method == 'GET':
        return render_template('join.html')
    elif request.method == 'POST':
        username = request.form.get("username")
        pattern = re.compile("^[A-Za-z]\w{4,24}$")
        if pattern.match(username) is None:
            flash('Usernames must be 5-25 letters and numbers, start with a letter', 'danger')
            return redirect(url_for('join'))
        if User.query.filter_by(username=username).first() != None:
            flash('That username already exists, try another', 'warning')
            return redirect(url_for('join'))
        pw1 = request.form.get("pw1")
        if len(pw1) < 6:
            flash ('Password must be at least 6 characters', 'danger')
            return redirect(url_for('join'))
        pw2 = request.form.get("pw2")
        if pw1 != pw2:
            flash('Those passwords are not the same', 'danger')
            return redirect(url_for('join'))
        new_user = User(username, pw1)
        db.session.add(new_user)
        db.session.commit()
        flash("Thanks! You can try logging in now.", 'info')
        return redirect(url_for('index'))

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    elif request.method == 'POST':
        form_username = request.form.get("username")
        the_user = User.query.filter_by(username=form_username).first()
        if the_user is None:
            flash("Hmm, I do not recognize that username", 'warning')
            return redirect(url_for('login'))
        if the_user.is_correct_password(request.form.get("pw")):
            flask_login.login_user(the_user)
            flash("Logged in.", 'success')
            return redirect(url_for('user_home'))
        flash("Hmm, that password is not correct", 'danger')
        return redirect(url_for('login'))

@app.route("/logout")
def logout():
    flask_login.logout_user()
    flash("You have logged out", 'info')
    return redirect(url_for('index'))

## Adminstration Routes
#################################################

@app.route("/mod")
@flask_login.login_required
@requires_mod
def mod_home():
    return render_template('mod.html')

@app.route("/mod/post")
@flask_login.login_required
@requires_mod
def mod_post():
    try:
        id = request.args.get('id')
    except:
        id = None
    if id:
        p = Post.query.get(id)
    else:
        p = Post.query.filter_by(mod_time=None).order_by(Post.create_time).first()
    return render_template('mod_post.html', post=p)

@app.route("/mod/post/<int:id>", methods=['POST'])
@flask_login.login_required
@requires_mod
def update_post(id):
    print request.form
    decision = request.form.get('approve')
    p = Post.query.get(id)
    p.isApproved = True if decision == "Approve" else False
    p.mod_time = datetime.now()
    db.session.add(p)
    db.session.commit()
    return redirect(url_for('mod_post'))


## Ship it!
#################################################

if __name__ == "__main__":
    app.run()
