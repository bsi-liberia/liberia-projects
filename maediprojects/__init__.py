from flask import Flask, Markup
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.babel import Babel
from flask.ext.mail import Mail
from flask.ext.login import login_required, current_user
import os
import mistune

app = Flask(__name__.split('.')[0])
app.config.from_pyfile(os.path.join('..', 'config.py'))
db = SQLAlchemy(app)
babel = Babel(app)
mail = Mail(app)

@app.template_filter("markdown")
def render_markdown(markdown_text):
    print markdown_text
    x = mistune.markdown(Markup(markdown_text), escape=False)
    print x
    return x

import routes

@babel.localeselector
def get_locale():
    return app.config["BABEL_DEFAULT_LOCALE"]
