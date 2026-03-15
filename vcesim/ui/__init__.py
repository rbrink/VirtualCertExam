import os
from flask import Flask
from flask.logging import default_handler
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from logging.config import dictConfig
from werkzeug.security import generate_password_hash

import vcesim.config.config as cfg
from vcesim.config.config import Config

# Setup logging, but because of werkzeug issues, we need to set up that later down file
dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s VCESIM: %(module)s.%(funcName)s %(message)s',
    }},
    'handlers': {
        'wsgi': {
            'class': 'logging.StreamHandler',
            'stream': 'ext://flask.logging.wsgi_errors_stream',
            'formatter': 'default'
        },
        "console": {"class": "logging.StreamHandler", "level": "INFO"},
        "null": {"class": "logging.NullHandler"},
    },
    'root': {
        'level': 'DEBUG',
        'handlers': ['wsgi']
    },
})

app = Flask(__name__)
app.config.from_object(Config)

csrf = CSRFProtect(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = "auth_bp.login"

# Set log level per arm.yml config
app.logger.info(f"Setting log level to: {cfg.vcesim_config['LOGLEVEL']}")
app.logger.setLevel(cfg.vcesim_config['LOGLEVEL'])

from . import routes
from vcesim.ui.auth.routes import auth_bp
from vcesim.ui.admin.routes import admin_bp
from vcesim.ui.students.routes import student_bp

app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(student_bp, url_prefix="/student")

from vcesim.models.user import User

with app.app_context():
    db.create_all()    # Create Databse
    # Check if default admin already exits
    if User.query.filter_by(username="admin").first():
        app.logger.warning(f"Admin user already exists, skipping...")
    else:
        default_admin = User(
            username="admin",
            email="admin@example.com",
            password_hash=generate_password_hash("password"),
            role="admin",
            must_change_password=True
        )
        db.session.add(default_admin)
        db.session.commit()
        app.logger.info(f"Default Admin created")

# Remove GET/page loads from logging
import logging
logging.getLogger('werkzeug').setLevel(logging.ERROR)
