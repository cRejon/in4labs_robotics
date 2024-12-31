class Config(object):
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