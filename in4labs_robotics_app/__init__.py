import os
import subprocess
import time
from datetime import datetime, timedelta, timezone

import pexpect
import requests
from flask import Flask, render_template, url_for, jsonify, redirect, send_file, flash, request
from flask_login import LoginManager, UserMixin, login_required, current_user, login_user

from .config import boards_config
from .utils import cleanLab, upload_sketch, update_boards_config, create_editor, create_navtab

# Docker environment variables
cam_url = os.environ.get('CAM_URL') 
user_email = os.environ.get('USER_EMAIL') 
end_time = os.environ.get('END_TIME') 

# The user end time will be 10 seconds before the actual end time
# to have some margin to clean the lab
user_end_time = datetime.strptime(end_time, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc) - timedelta(seconds=10)

boards = update_boards_config(boards_config)

app = Flask(__name__, instance_path=os.path.join(os.getcwd(), 'arduino'))
# Flask environment variable needed for session management
flask_config = {
    # Use as secret key the user email + the end time of the session 
    'SECRET_KEY': user_email + end_time,
}
app.config.from_mapping(flask_config)

# Start the thread to clean the lab
clean_lab = cleanLab(boards, user_end_time, app.instance_path)
clean_lab.start()

# Create the subfolders for the compilations
try:
    for board in boards.keys():
        os.makedirs(os.path.join(app.instance_path, 'compilations', board))
        for dir in ['build', 'cache', 'temp_sketch']:
            os.makedirs(os.path.join(app.instance_path, 'compilations', board, dir))
except OSError:
    pass

# Flask-Login configuration
login_manager = LoginManager()
login_manager.login_view = 'login' # Set the default login page
login_manager.init_app(app)

@login_manager.user_loader
def load_user(id):
    return user

class User(UserMixin):
    def __init__(self, id, email):
        self.id = id
        self.email = email

user = User(id=1, email=user_email)


# Flask routes
@app.route('/', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index')) 

    if request.method == 'POST':
        email = request.form['email']
        if email == user_email:
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Invalid email address. Please try again.')
    
    return render_template('login.html')

@app.route('/index')
@login_required
def index():
    navtabs = []
    editors = []
    for board in boards.items():
        navtabs.append(create_navtab(board))
        editors.append(create_editor(board))
    return render_template('index.html', boards=boards, navtabs=navtabs,
                                editors=editors, cam_url=cam_url, 
                                end_time=user_end_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ'))

@app.route('/get_example', methods=['GET'])
@login_required
def get_example(): 
    example = request.args.get('example')      
    examples_path = os.path.join(app.instance_path, 'examples')
    example_file = None
    
    # Find example file in the corresponding folder
    for folder in os.listdir(examples_path):
        if example in os.listdir(os.path.join(examples_path, folder)):
            example_file = os.path.join(examples_path, folder, example)
            break

    return send_file(example_file, mimetype='text')

@app.route('/compile', methods=['POST'])
@login_required
def compile():
    board = request.form['board']
    code = request.form['text']

    fqbn = boards[board]['fqbn']

    compilation_path = os.path.join(app.instance_path, 'compilations', board)
    sketch_path = os.path.join(compilation_path, 'temp_sketch')

    with open(os.path.join(sketch_path, 'temp_sketch.ino'), 'w') as f:
        f.write(code)

    command = ['arduino-cli', 'compile', '--fqbn', fqbn,
        '--build-cache-path', os.path.join(compilation_path, 'cache'), 
        '--build-path', os.path.join(compilation_path, 'build'), 
        sketch_path]

    result = subprocess.run(command, capture_output=True, text=True) 

    resp = jsonify(board=board, error=result.stderr)
    return resp

@app.route('/execute', methods=['POST'])
@login_required
def execute():
    global boards

    board = request.form['board']
    target = request.form['target']
    
    usb_driver = boards[board]['usb_driver']
    fqbn = boards[board]['fqbn']

    result = upload_sketch(board, fqbn, usb_driver, target)

    resp = jsonify(board=board, error=result.stderr)
    return resp

@app.route('/monitor', methods=['GET'])
@login_required
def monitor():
    global boards
    
    board = request.args.get('board')
    baudrate = request.args.get('baudrate', default=9600, type=int)
    seconds = request.args.get('seconds', default=10, type=int)

    usb_driver = boards[board]['usb_driver']

    command = f'arduino-cli monitor -p /dev/{usb_driver} --quiet --config baudrate={baudrate}'
    # NOTE: pexpect is used because arduino-cli monitor expects to run in an interactive 
    #       terminal environment and subprocess.run() does not work properly.
    child = pexpect.spawn(command)
    
    try:
        child.expect(pexpect.EOF, timeout=seconds)
    except pexpect.TIMEOUT:
        pass

    output = child.before.decode('utf-8')
    
    child.close()
        
    resp = jsonify(board=board, output=output)
    return resp

@app.route('/suggest', methods=['POST'])
@login_required
def suggest():
    board = request.form['board']
    code = request.form['text']

    data = {'action': '16', 'text': code}
    url = 'https://open.ieec.uned.es/v_innovacion/api.php'

    r = requests.post(url, data=data)
    suggestion = r.text

    resp = jsonify(board=board, suggestion=suggestion)
    return resp

@app.route('/reset_lab', methods=['GET'])
@login_required
def reset():
    global boards
    
    # Uhubctl is used to power on/off the USB ports of the Raspberry Pi
    command = ['uhubctl', '-a', 'cycle', '-l', '1-1', '-d', '2']
    result = subprocess.run(command, capture_output=True, text=True)
    
    # Load the stop code in all the boards
    time.sleep(1)
    for board in boards:
        usb_driver = boards[board]['usb_driver']
        fqbn = boards[board]['fqbn']
        upload_sketch(board, fqbn, usb_driver, 'stop', app.instance_path)
    # Return the output of the command for debugging purposes
    resp = jsonify(result=result.stdout)
    return resp

