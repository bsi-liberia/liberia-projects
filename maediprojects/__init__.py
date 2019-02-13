from flask import Flask, Markup
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_babel import Babel
from flask_mail import Mail
from flask_login import login_required, current_user
import os
import mistune

from . import commands


def register_commands(app):
    """Register Click commands."""
    app.cli.add_command(commands.setup)
    app.cli.add_command(commands.setup_country)
    app.cli.add_command(commands.import_liberia)
    app.cli.add_command(commands.import_psip)


app = Flask(__name__.split('.')[0])
app.config.from_pyfile(os.path.join('..', 'config.py'))
register_commands(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
babel = Babel(app)
mail = Mail(app)

@app.template_filter("markdown")
def render_markdown(markdown_text):
    return mistune.markdown(Markup(markdown_text), escape=False)

import routes

@babel.localeselector
def get_locale():
    return app.config["BABEL_DEFAULT_LOCALE"]
