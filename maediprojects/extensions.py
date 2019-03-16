from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_babel import Babel
from flask_mail import Mail
from flask_login import LoginManager
from flask_babel import gettext


db = SQLAlchemy()
migrate = Migrate()
babel = Babel()
mail = Mail()

login_manager = LoginManager()
login_manager.login_view = "users.login"
login_manager.login_message = gettext(u"Please log in to access this page.")
login_manager.login_message_category = "danger"
