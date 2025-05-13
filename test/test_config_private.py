from tempfile import mkdtemp
import os


basedir = os.path.abspath(os.path.dirname(__file__))
nodered_dir = os.path.join(basedir, os.pardir, 'node-red')
nodered_settings_file = os.path.join(nodered_dir, 'settings.js')

class Config(object):
    
    # Flask settings
    ENV = 'development'
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 600
    SECRET_KEY = 'top-secret-key-for-in4labs',
    SESSION_TYPE= 'filesystem',
    SESSION_FILE_DIR = mkdtemp(),
    SESSION_COOKIE_NAME = 'cookie-app-sessionid-in4labs'
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
            'cam_url': 'http://62.204.201.51:8100/Mjpeg/0?authToken=2454ef16-84cf-4184-a748-8bddd993c078',

        }],
    }