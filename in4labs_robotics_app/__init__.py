import os
from datetime import datetime, timedelta, timezone

from flask import Flask
from flask_login import LoginManager

from .config import Config
from .utils import User, cleanLab, update_boards_config


url_prefix = '/' + Config.server_name + '/' + Config.lab_name
# The user end time will be 10 seconds before the actual end time
# to have some margin to clean the lab
user_end_time = datetime.strptime(Config.end_time, "%Y-%m-%dT%H:%M:%S.%fZ")\
    .replace(tzinfo=timezone.utc) - timedelta(seconds=10)

boards = update_boards_config(Config.boards_config)

app = Flask(__name__, instance_path=os.path.join(os.getcwd(), 'arduino'),
            static_url_path=(url_prefix+'/static/'))
app.config.from_mapping(Config.flask_config)

# Start the thread to clean the lab
clean_lab = cleanLab(boards, user_end_time, app.instance_path)
clean_lab.start()

# Flask-Login configuration
login_manager = LoginManager()
login_manager.login_view = 'lab.login' # Set the default login page
login_manager.init_app(app)

# Single User instance and loader
user = User(id=1, email=Config.user_email)

@login_manager.user_loader
def load_user(user_id):
    return user

# Create the subfolders for the compilations
try:
    for board in boards.keys():
        os.makedirs(os.path.join(app.instance_path, 'compilations', board))
        for dir in ['build', 'cache', 'temp_sketch']:
            os.makedirs(os.path.join(app.instance_path, 'compilations', board, dir))
except OSError:
    pass

# Register blueprints - moved to the end to avoid circular imports
def register_blueprints():
    from .lab_bp import bp
    app.register_blueprint(bp, url_prefix=url_prefix)

register_blueprints()
