import os
import re
import subprocess
import threading
import time
from datetime import datetime, timedelta, timezone
import atexit

import bcrypt
import docker

from test_config import Config


basedir = os.path.abspath(os.path.dirname(__file__))

# Class to stop the containers when the time is up
class StopContainersTask(threading.Thread):
     def __init__(self, containers, end_time):
         super(StopContainersTask, self).__init__()
         self.containers = containers
         self.end_time = end_time
 
     def run(self):
        remaining_secs = (end_time - datetime.now()).total_seconds()
        time.sleep(remaining_secs)
        for container in self.containers:
            container.stop()
        print('Lab containers stopped.')

# Function to create a Docker image from a Dockerfile
def create_docker_image(image_name, dockerfile_path):
    print(f'Creating Docker image {image_name}. Be patient, this will take a while...')
    image, build_logs = client.images.build(
        path=dockerfile_path,
        tag=image_name,
        rm=True,
    )
    for log in build_logs: # Print the build logs for debugging purposes
        print(log.get('stream', '').strip())
    print(f'Docker image {image_name} created successfully.')

# Import lab config from Config object
lab_duration = Config.labs_config['duration']
lab = Config.labs_config['labs'][0]
lab_name = lab['lab_name']
lab_image_name = f'{lab_name.lower()}:latest'
host_port = lab['host_port']

# Export DOCKER_HOST environment variable to run in rootless mode
os.environ['DOCKER_HOST'] = 'unix:///run/user/1000/docker.sock'

# Create docker lab image if not exists
client = docker.from_env()
try:
    client.images.get(lab_image_name)
    print(f'Docker image {lab_image_name} already exists.')
except docker.errors.ImageNotFound:
    lab_dockerfile_path = os.path.join(basedir, os.pardir)
    create_docker_image(lab_image_name, lab_dockerfile_path)

# Create or pull images in extra_containers
extra_containers = lab.get('extra_containers', [])
for container in extra_containers:
    image_name = container['image']
    try:
        client.images.get(image_name)
        print(f'Docker image {image_name} already exists.')
    except docker.errors.ImageNotFound:
        if container['name'] == 'node-red':
            # Create the node-red image
            nodered_dockerfile_path = os.path.join(basedir, os.pardir, 'node-red')
            create_docker_image(image_name, nodered_dockerfile_path)
        else:
            print(f'Pulling Docker image {image_name}. Be patient, this will take a while...')
            client.images.pull(image_name)
            print(f'Docker image {image_name} pulled successfully.')
    
    # Create network 
    network_name = container['network']
    try:
        client.networks.get(network_name)
        print(f'Docker network {network_name} already exists.')
    except docker.errors.NotFound:
        print(f'Creating Docker network {network_name}.')
        client.networks.create(network_name)
        print(f'Docker network {network_name} created successfully.')

    # Create volumes
    volumes = container.get('volumes', {})
    for volume_name, volume in volumes.items():
        # Check if volume_name not starts with '/', so it is a volume and not a path
        if not volume_name.startswith('/'):
            try:
                client.volumes.get(volume_name)
                print(f'Docker volume {volume_name} already exists.')
            except docker.errors.NotFound:
                print(f'Creating Docker volume {volume_name}.')
                client.volumes.create(volume_name)
                print(f'Docker volume {volume_name} created successfully.')

print('All Docker images, networks and volumes are ready.')

# Get the Raspberry pi IP address
hostname = subprocess.check_output(['hostname', '-I']).decode("utf-8").split()[0]
nodered_nat_port = lab['extra_containers'][0]['nat_port']

# Docker environment variables
end_time = datetime.now(timezone.utc) + timedelta(minutes=lab_duration)
docker_env = {
    'USER_EMAIL': 'admin@email.com',
    'USER_ID': 1,
    'END_TIME': end_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
    'CAM_URL': lab.get('cam_url', ''),
    'NODE_RED_URL': f'http://{hostname}:{nodered_nat_port}',
}

containers = []
# Start the extra containers
for extra_container in extra_containers:
    
    if extra_container['name'] == 'node-red':
        # Clean the volume for the new user
        volume_name = 'integration_lab_vol'
        volume = client.volumes.get(volume_name)
        volume.remove()
        client.volumes.create(volume_name)

        # Set the username and password for the node-red container
        nodered_dir = os.path.join(basedir, os.pardir, 'node-red')
        username = "admin@email.com"
        # Generate bcrypt hash from the username
        hashed_password = bcrypt.hashpw(username.encode(), bcrypt.gensalt()).decode()
        # Copy the default settings file
        settings_default_file = os.path.join(nodered_dir, 'settings_default.js')
        with open(settings_default_file, 'r') as file:
            js_content = file.read()
        # Use regular expressions to find and replace the username and password
        username_pattern = r'username:\s*"[^"]*"'
        password_pattern = r'password:\s*"[^"]*"'
        new_username_line = f'username: "{username}"'
        new_password_line = f'password: "{hashed_password}"'
        js_content = re.sub(username_pattern, new_username_line, js_content)
        js_content = re.sub(password_pattern, new_password_line, js_content)
        # Write the modified content in a settings.js file
        settings_file = os.path.join(nodered_dir, 'settings.js')
        with open(settings_file, 'w') as file:
            file.write(js_content)

    container_extra = client.containers.run(
                    extra_container['image'], 
                    name=extra_container['name'],
                    detach=True, 
                    remove=True,
                    network=extra_container['network'],
                    ports=extra_container['ports'],
                    volumes=extra_container.get('volumes', {}),
                    command=extra_container.get('command', ''))
    containers.append(container_extra)

# Run the lab container
container_lab = client.containers.run(
                lab_image_name, 
                detach=True, 
                remove=True,
                privileged=True,
                ports={'8000/tcp': ('0.0.0.0', host_port)}, 
                volumes=lab.get('volumes', {}),
                environment=docker_env)
containers.append(container_lab)

stop_container = StopContainersTask(containers, end_time)
stop_container.start()


lab_url = f'http://{hostname}:{host_port}'
print(f'The container is running at {lab_url} during {lab_duration} minutes.')

# Stop the containers when the program exits by pressing Ctrl+C
def exit_handler():
    # Check if the containers are still running
    for container in containers:
        try:
            container.stop()
        except:
            pass

atexit.register(exit_handler)



