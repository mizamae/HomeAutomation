

# Nginx configuration for HomeAutomation

[Nginx][0] is an application that 

## Installation

### Quick start

To install Nginx on a Linux environment, type the following command:

    sudo apt-get install nginx

Once properly installed, it is automatically started once the system is booted. 
Nginx looks for incoming connections through the port and to the domains indicated in its configuration file. These files are usually placed in the path '/etc/nginx/sites-available/project'. A working example of this configuration file is the HomeAutomation.nginxconf file included here.

In order to activate the configuration file, the following steps are to be followed:
   1. Copy the configuration file to the path indicated
   2. Create a link of the file in the sites-enabled path from Nginx
			
		sudo ln -s /etc/nginx/sites-available/HomeAutomation /etc/nginx/sites-enabled  

   3. Test the configuration running
 		
		sudo nginx -t				
	
   4. If no errors are found, restart Nginx and you should be able to see the Nginx .
   
		sudo systemctl restart nginx

A more detailed but general manual about configuring Nginx can be found [here][1]	

### Detailed instructions

## Generation of user and passw pairs to accept or deny the publication of location data
Details are shown [here][2]
    1. Verify that apache2-utils are installed.
    	
    	sudo apt-get install apache2-utils

    2. Create a password file and a first user
    
        sudo htpasswd -c /etc/apache2/.htpasswd user1
        
    3. In the same way create other user-password pairs

To get a summary of the access types registered by Nginx. This can help you in finding if somebody it trying to access.

	awk '{print $9}' /var/log/nginx/access.log | sort | uniq -c | sort -rn
To get the pages with broken link (404)

	 awk '($9 ~ /404/)' /var/log/nginx/access.log | awk '{print $7}' | sort | uniq -c | sort -rn
Take a look at the docs for more information.

[0]: https://nginx.org/en/
[1]: https://www.digitalocean.com/community/tutorials/how-to-set-up-django-with-postgres-nginx-and-gunicorn-on-ubuntu-16-04
[2]: https://www.nginx.com/resources/admin-guide/restricting-access-auth-basic/