In4Labs - Robotics Systems remote lab [![CC BY-NC-SA 4.0][cc-by-nc-sa-shield]][cc-by-nc-sa]
=====
# Description
Implementation of the Robotics Systems lab inside a Docker image that will be run by the tools [In4Labs base LTI tool](https://github.com/cRejon/in4labs) (if using a LMS such as Moodle) or [In4Labs base auth tool](https://github.com/cRejon/in4labs_auth) (if basic authentication is desired).  
Tested on Raspberry Pi OS Lite Bullseye (64-bit). Requires Python >=3.9.

# Installation
This lab uses an [Arduino UNO R3](https://docs.arduino.cc/hardware/uno-rev3/) board to perform the experiments. Connect the board to the Raspberry Pi according to its **_'usb_port'_** variable inside the app _config.py_ file. This variable can be changed if more laboratories are installed on the same Raspberry Pi.
```
# Boards configuration
boards = {
    'Board_1':{
        'name':'UNO R3',
        'model':'Arduino UNO Rev3',
        'fqbn':'arduino:avr:uno',
        'usb_port':'1',
    }
}
```
If you look at the USB hub from the front, the port numbering is as follows.

                _______    _______ 
               | _____ |  | _____ | 
        3-->   ||_____||  ||_____||  <-- 1
               | _____ |  | _____ | 
        4-->   ||_____||  ||_____||  <-- 2
               |_______|__|_______|

# Testing
## Setup Raspberry Pi
### Docker installation
1. Install Docker through its bash script selecting the version to **25.0.5**:
```
sudo apt update
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh --version 25.0.5
```
2. Manage Docker as a non-root user:
``` 
sudo groupadd docker
sudo usermod -aG docker $USER
newgrp docker
```
### Python packages
```
sudo apt install -y python3-docker
```
## Running
Execute the **_test.py_** file inside _test folder_ and go in your browser to the given url.  
The Docker container is created via the Dockerfile <ins>only</ins> the first time this script is run. This will take some time, so please be patient.  
On the login page, enter ```admin@email.com``` as user.
# License
This work is licensed under a
[Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License][cc-by-nc-sa].

[![CC BY-NC-SA 4.0][cc-by-nc-sa-image]][cc-by-nc-sa]

[cc-by-nc-sa]: http://creativecommons.org/licenses/by-nc-sa/4.0/
[cc-by-nc-sa-image]: https://licensebuttons.net/l/by-nc-sa/4.0/88x31.png
[cc-by-nc-sa-shield]: https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg
