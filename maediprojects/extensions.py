from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_babel import Babel
from flask_mail import Mail
from flask_jwt_extended import JWTManager
from flask_login import LoginManager, AnonymousUserMixin
from flask_babel import gettext


db = SQLAlchemy()
migrate = Migrate()
babel = Babel()
mail = Mail()

jwt = JWTManager()
login_manager = LoginManager()
login_manager.login_view = "users.login"
login_manager.login_message = gettext(u"Please log in to access this page.")
login_manager.login_message_category = "danger"

class UnauthenticatedUser(AnonymousUserMixin):
    def as_simple_dict(self):
        return (
            {c: getattr(self, c) for c in [
                'username', 'administrator', 'name',
                'permissions_list', 'roles_list',
                'email_address', 'permissions_dict'
            ]}
        )
    def __init__(self):
        self.username = None
        self.administrator = False
        self.name = None
        self.permissions_list = {
            "edit": "none",
            "organisations": {},
            "view": "external"
        }
        self.roles_list = []
        self.email_address = None
        self.permissions_dict = {
            "edit": "none",
            "organisations": {},
            "view": "external"
        }

login_manager.anonymous_user = UnauthenticatedUser