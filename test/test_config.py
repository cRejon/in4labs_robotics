class Config(object):   
        # Labs settings
    labs_config = {
        'server_name': 'test_server',
        'mountings': [{
            'id': '3', 
            'duration': 10, # minutes
            'cam_url': 'https://ULR_TO_WEBCAM/stream.m3u8',
        },],
        'labs': [{
            'lab_name' : 'in4labs_robotics',
            'html_name' : 'Robotics Laboratory',
            'description' : 'In4Labs laboratory for robotics systems.',
            'mounting_id': '3',
            'host_port' : 8005,
        }],
    }