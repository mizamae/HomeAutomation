

# Daphne configuration for HomeAutomation

[Daphne][0] is an HTTP, HTTP2 and WebSocket protocol server for ASGI, and developed to power Django Channels.

## Installation

See the Channels' [docs][1] for a detailed explanation of everything.

### Quick start

To install Daphne on a Linux environment, type the following command:

    sudo apt-get install daphne

In order to use a Redis backend, Redis should also need to be installed:

    sudo pip install -U asgi_redis

Once properly installed, the process needs to be configured to target the required Django application and Nginx interface. Additionally, it also needs to be started whenever the system reboots (as it does not start automatically).
In order to do both things at the same time, the following steps are to be followed:

   1. Copy the configuration file [daphne.service] to the path '/etc/systemd/system/'
   
		1.1 You can do this by creating a new text file with the command:
		sudo nano /etc/systemd/system/daphne.service

		1.2 Or copying the file included here using the command
		sudo mv /source_folder/daphne.service  /etc/systemd/system/	
   		
   2. Now the Daphne service created can be started and enabled it to automatically start at boot
			
		sudo systemctl start daphne 
		sudo systemctl enable daphne

If everything went fine, a socket file 'HomeAutomation_RT.sock' should have been created at the path setup in the daphne.service file ('/home/pi/run/' in this case). Additionally, the status of the Daphne process can be monitored using the following command:
 		
		sudo journalctl -u daphne				
	
Using this last command, some debugging information for the HomeAutomation application can be yielded.
   
### Important information
It is very important to place the Django application files in a folder were the user (pi in this case) has all the permissions. In this case, the Django files are placed in '/home/pi/HomeAutomation'

After any change in Django files, it is required to restart the gunicorn service as:

	sudo systemctl restart daphne

### Detailed instructions

Take a look at the docs for more information.

[0]: https://github.com/django/daphne
[1]: http://channels.readthedocs.io/en/stable/deploying.html