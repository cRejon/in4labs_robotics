from tempfile import mkdtemp
import os


basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    
    # Flask settings
    ENV = 'development'
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 600
    SECRET_KEY = 'replace-me', # change in production
    SESSION_TYPE= 'filesystem',
    SESSION_FILE_DIR = mkdtemp(),
    SESSION_COOKIE_NAME = 'app-sessionid' 
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = False   # should be True in case of HTTPS usage (production)
    SESSION_COOKIE_SAMESITE = None  # should be 'None' in case of HTTPS usage (production)
    DEBUG_TB_INTERCEPT_REDIRECTS = False

    # Labs settings
    labs_config = {
        'duration': 15, # minutes
        'labs': [{
            'lab_name' : 'in4labs_robotics',
            'html_name' : 'Robotics Laboratory',
            'description' : 'In4Labs laboratory for robotics systems.',
            'host_port' : 8001,
            'volumes': {'/dev/bus/usb': {'bind': '/dev/bus/usb', 'mode': 'rw'},
                        'integration_lab_vol': {'bind': '/app/node-red/data', 'mode': 'ro'}},
            'cam_url': 'http://ULR_TO_WEBCAM/Mjpeg',
        }],
    }