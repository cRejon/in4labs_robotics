import os


class Config(object):
    # Boards configuration
    boards_config = {
        'Board_1':{
            'name':'UNO R3',
            'model':'Arduino UNO Rev3',
            'fqbn':'arduino:avr:uno',
            'usb_port':'1',
        }
    }

    # Docker environment variables
    server_name = os.environ.get('SERVER_NAME')
    lab_name = os.environ.get('LAB_NAME')
    user_email = os.environ.get('USER_EMAIL') 
    end_time = os.environ.get('END_TIME') 
    cam_url = os.environ.get('CAM_URL') 

    # Flask environment variable needed for session management
    flask_config = {
        # Use as secret key the user email + the end time of the session 
        'SECRET_KEY': user_email + end_time,
        'SESSION_COOKIE_NAME': user_email + end_time,
    }
