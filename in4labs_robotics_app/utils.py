import os
import subprocess
import re
import threading
import time
from datetime import datetime, timezone

from flask import current_app
from flask_login import UserMixin


class User(UserMixin):
    def __init__(self, id, email):
        self.id = id
        self.email = email
      
# Class to clean the lab before and after the user session
class cleanLab(threading.Thread):
    def __init__(self, boards, user_end_time, instance_path):
        super(cleanLab, self).__init__()
        self.boards = boards
        self.user_end_time = user_end_time
        self.instance_path = instance_path # It's not possible to access current_app inside a thread

    def clean(self):
        for board_conf in self.boards.items():
            upload_sketch(board_conf, 'stop', self.instance_path)
 
    def run(self):
        self.clean()
        remaining_secs = (self.user_end_time - datetime.now(timezone.utc)).total_seconds()
        if (remaining_secs > 0):
            time.sleep(remaining_secs)
            self.clean()    

# Function to get the serial number and USB driver of the boards 
# depending on the USB port they are connected to
def update_boards_config(boards_config):
    result = subprocess.run(['dmesg'], capture_output=True, text=True)
    dmesg_output = result.stdout

    # Get serial numbers
    pattern_serial = r'1-1.(\d): SerialNumber:\s(.*?)\n'
    matches_serial = re.findall(pattern_serial, dmesg_output)
    for match in matches_serial:
        for config in boards_config.values():
            if config['usb_port'] == match[0]:
                config['serial_number'] = match[1]
                break
    
    # Raise an exception if a board is not connected
    for config in boards_config.values():
        if config.get('serial_number') is None:
            raise Exception(f'Board with USB port {config["usb_port"]} is not connected')
        
    # Get USB drivers
    pattern_usb = r'1-1.(\d).*?(tty\w\w\w\d)'
    matches_usb = re.findall(pattern_usb, dmesg_output)
    for match in matches_usb:
        for config in boards_config.values():
            if config['usb_port'] == match[0]:
                config['usb_driver'] = match[1]
                break

    return boards_config

def upload_sketch(board_conf, target, instance_path=None):
    # Use current_app.instance_path if instance_path is not provided
    path = instance_path or current_app.instance_path
    
    board = board_conf[0]
    config = board_conf[1]

    fqbn = config['fqbn']
    usb_driver = config['usb_driver']

    if (target == 'user'): 
        input_file = os.path.join(path, 'compilations', board, 'build','temp_sketch.ino.hex')
    else: # target == 'stop'
        input_file = os.path.join(path, 'compilations', 'precompiled','stop.ino.hex')

    command = ['arduino-cli', 'upload', '--port', f'/dev/{usb_driver}',
                 '--fqbn', fqbn, '--input-file', input_file]
    
    result = subprocess.run(command, capture_output=True, text=True) 
    return(result)  