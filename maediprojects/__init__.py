from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.babel import Babel
from flask.ext.mail import Mail
import os

app = Flask(__name__.split('.')[0])
app.config.from_pyfile(os.path.join('..', 'config.py'))
db = SQLAlchemy(app)
babel = Babel(app)
mail = Mail(app)

import routes

@babel.localeselector
def get_locale():
    return app.config["BABEL_DEFAULT_LOCALE"]
