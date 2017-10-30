

# Gunicorn configuration for HomeAutomation

[Gunicorn][0] is an application that behaves as an interface between the Nginx server and your Django application.

## Installation

### Quick start

To install Gunicorn on a Linux environment, type the following command:

    sudo apt-get install gunicorn

Once properly installed, the process needs to be configured to target the required Django application and Nginx interface. Additionally, it also needs to be started whenever the system reboots (as it does not start automatically).
In order to do both things at the same time, the following steps are to be followed:

   1. Copy the configuration file [gunicorn.service] to the path '/etc/systemd/system/'
   
		1.1 You can do this by creating a new text file with the command:
		sudo nano /etc/systemd/system/gunicorn.service

		1.2 Or copying the file included here using the command
		sudo mv /source_folder/gunicorn.service  /etc/systemd/system/	
   		
   2. Now the Gunicorn service created can be started and enabled it to automatically start at boot
			
		sudo systemctl start gunicorn 
		sudo systemctl enable gunicorn

If everything went fine, a socket file 'HomeAutomation.sock' should have been created at the path setup in the gunicorn.service file ('/home/pi/run/' in this case). Additionally, the status of the Gunicorn process can be monitored using the following command:
 		
		sudo journalctl -u gunicorn				
	
Using this last command, some debugging information for the HomeAutomation application can be yielded.
   
### Important information
It is very important to place the Django application files in a folder were the user (pi in this case) has all the permissions. In this case, the Django files are placed in '/home/pi/HomeAutomation'

After any change in Django files, it is required to restart the gunicorn service as:

	sudo systemctl restart gunicorn

### Detailed instructions

Take a look at the docs for more information.

[0]: http://docs.gunicorn.org/en/stable/index.html
