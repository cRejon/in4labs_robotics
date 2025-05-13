import os
import subprocess
import time
from datetime import datetime, timezone, timedelta

import pexpect
import requests
from flask import current_app, render_template, jsonify, send_file, request, url_for, redirect, flash
from flask_login import current_user, login_user, login_required

from in4labs_perception_app import boards, user, user_end_time
from in4labs_perception_app.lab_bp import bp
from .utils import create_editor, create_navtab
from ..utils import upload_sketch
from ..config import Config


# Default route for login
@bp.route('/', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('lab.index')) 

    if request.method == 'POST':
        email = request.form['email']
        if email == user.email:
            login_user(user)
            return redirect(url_for('lab.index'))
        flash('Invalid email address. Please try again.')
    
    return render_template('login.html')

@bp.route('/index')
@login_required
def index():
    navtabs = []
    editors = []
    for board_conf in boards.items():
        navtabs.append(create_navtab(board_conf))
        editors.append(create_editor(board_conf))
    return render_template('index.html', boards=boards, navtabs=navtabs,
                                editors=editors, cam_url=Config.cam_url, 
                                end_time=user_end_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ'))

@bp.route('/get_example', methods=['GET'])
@login_required
def get_example(): 
    board = request.args.get('board')
    example = request.args.get('example')      
    
    examples_path = os.path.join(current_app.instance_path, 'examples')
    board_path = os.path.join(examples_path, board)
    commons_path = os.path.join(examples_path, 'Commons')
    
    example_file = None
    for path in [board_path, commons_path]:
        if os.path.isdir(path) and example in os.listdir(path):
            example_file = os.path.join(path, example)
            break

    return send_file(example_file, mimetype='text')

@bp.route('/compile', methods=['POST'])
@login_required
def compile():
    board = request.form['board']
    code = request.form['text']

    fqbn = boards[board]['fqbn']
        
    compilation_path = os.path.join(current_app.instance_path, 'compilations', board)
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

@bp.route('/execute', methods=['POST'])
@login_required
def execute():
    board = request.form['board']
    target = request.form['target']
    
    for board_conf in boards.items():
        if board_conf[0] == board:
            result = upload_sketch(board_conf, target)
            break 
    
    resp = jsonify(board=board, error=result.stderr)
    return resp

@bp.route('/monitor', methods=['GET'])
@login_required
def monitor():
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

@bp.route('/suggest', methods=['POST'])
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

@bp.route('/reset_lab', methods=['GET'])
@login_required
def reset():
    # Uhubctl is used to power on/off the USB ports of the Raspberry Pi
    command = ['uhubctl', '-a', 'cycle', '-l', '1-1', '-d', '2']
    result = subprocess.run(command, capture_output=True, text=True)
    
    # Load the stop code in all the boards
    time.sleep(1)
    for board_conf in boards.items():
        upload_sketch(board_conf, 'stop')
    
    # Return the output of the command for debugging purposes
    resp = jsonify(result=result.stdout)
    return resp