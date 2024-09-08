import os
import subprocess
import time

import pexpect
import requests
from flask import Flask, render_template, url_for, jsonify, redirect, send_file, flash, request
from flask_login import LoginManager, UserMixin, login_required, current_user, login_user

from .utils import get_serial_number, get_usb_driver, create_editor, create_navtab


# Flask environment variable needed for session management
flask_config = {
    # Use as secret key the user email + the end time of the session 
    'SECRET_KEY': os.environ.get('USER_EMAIL') + os.environ.get('END_TIME'),
}

# Docker environment variables
cam_url = os.environ.get('CAM_URL') 
user_email = os.environ.get('USER_EMAIL') 
end_time = os.environ.get('END_TIME') 

# Boards configuration
boards = {
    'Board_1':{
        'name':'UNO R3',
        'model':'Arduino UNO Rev3',
        'fqbn':'arduino:avr:uno',
        'usb_port':'1',
    }
}

boards = get_serial_number(boards) # Get the serial number and driver of the boards

app = Flask(__name__, instance_path=os.path.join(os.getcwd(), 'arduino'))
app.config.from_mapping(flask_config)

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
                                editors=editors, cam_url=cam_url, end_time=end_time)

@app.route('/get_example', methods=['GET'])
@login_required
def get_example(): 
    example = request.args.get('example')      
    examples_path = os.path.join(app.instance_path, 'examples')

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

    compilation_path = os.path.join(app.instance_path, 'compilations', board)
    sketch_path = os.path.join(compilation_path, 'temp_sketch')

    with open(os.path.join(sketch_path, 'temp_sketch.ino'), 'w') as f:
        f.write(code)

    command = ['arduino-cli', 'compile', '--fqbn', boards[board]['fqbn'],
    '--build-cache-path', os.path.join(compilation_path, 'cache'), 
    '--build-path', os.path.join(compilation_path, 'build'), 
    sketch_path]

    result = subprocess.run(command, capture_output=True, text=True) 

    resp = jsonify(board=board, error=result.stderr)
    return resp

@app.route('/execute', methods=['POST'])
@login_required
def execute():
    board = request.form['board']
    target = request.form['target']

    upload_sketch(board, target)

    resp = jsonify(board=board)
    return resp

def upload_sketch(board, target):
    global boards
    boards = get_usb_driver(boards) # Get the drivers (ttyACM*) of the boards
    
    usb_driver = boards[board]['usb_driver']
    fqbn = boards[board]['fqbn']

    if (target == 'user'): 
        input_file = os.path.join(app.instance_path, 'compilations', board, 'build','temp_sketch.ino.hex')
    else: # target == 'stop'
        input_file = os.path.join(app.instance_path, 'compilations', 'precompiled','stop.ino.hex')

    command = ['arduino-cli', 'upload', '--port', f'/dev/{usb_driver}',
                 '--fqbn', fqbn, '--input-file', input_file]
    
    result = subprocess.run(command, capture_output=True, text=True) 
    print(result) # Debug info


@app.route('/monitor', methods=['GET'])
@login_required
def monitor():
    global boards
    boards = get_usb_driver(boards) # Get the drivers (ttyACM*) of the boards
    
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
    # Uhubctl is used to power on/off the USB ports of the Raspberry Pi
    command = ['uhubctl', '-a', 'cycle', '-l', '1-1', '-d', '2']
    result = subprocess.run(command, capture_output=True, text=True)
    # Load the stop code in all the boards
    time.sleep(1)
    for board in boards:
        upload_sketch(board, 'stop')
    # Return the output of the command for debugging purposes
    resp = jsonify(result=result.stdout)
    return resp

