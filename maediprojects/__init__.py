from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
import os

app = Flask(__name__.split('.')[0])
app.config.from_pyfile(os.path.join('..', 'config.py'))
db = SQLAlchemy(app)

import routes