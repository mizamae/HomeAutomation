Download the OS iso file from respository
Copy it with Etcher to the SD.
Create a file named SSH in the root of SD to enable ssh by default.
Introduce the SD into the RasPi

Update apt

	sudo apt-get update
	sudo apt-get upgrade

Install pip

	sudo apt-get install python3-pip

Make python3 as standard

	sudo ln -sf /usr/bin/python3 /usr/bin/python

Install dependencies for Pillow image library

	sudo apt-get install libopenjp2-7-dev
	sudo apt-get install libjpeg-dev
	sudo apt-get install libtiff4
	sudo apt-get install libjpeg8-dev zlib1g-dev
	sudo apt-get install libfreetype6-dev liblcms2-dev libwebp-dev tcl8.5-dev tk8.5-dev python-tk

Install Pandas

	sudo apt-get install python3-pandas
	sudo apt-get install python3-numpy python3-scipy
	sudo easy_install --upgrade pytz

Install redis-server
	
	sudo apt-get install redis-server
	pip install django-redis

Clone the HomeAutomation repository from Github
	
	sudo apt-get install git
	git clone https://github.com/mizamae/HomeAutomation.git

Do remember to modify the ALLOWED_HOSTS variable from settings.production

Install python packages

	sudo pip3 install -r requirements.txt
	
Install daphne and worker and gunicorn services

Make and Apply migrations

	python utils/migrations_handler.py make *
	python utils/migrations_handler.py migrate

Create SuperUser manually from the shell

	python utils/create_SuperUser.py
	
Or use this Shell script 

	#!/bin/bash
	echo "from authtools.models import User; \
	User.objects.filter(email='defaultSuperUser@diy4dot0.net').delete(); \
	User.objects.create_superuser(name='Mikel',email='defaultSuperUser@diy4dot0.net',password='diy4dot0')" \
	| python HomeAutomation/src/manage.py shell
	# create_superuser(name,email,password)

Install Nginx
	
	sudo apt-get install nginx
	
Copy configuration file to sites-available folder

	sudo mv HomeAutomation.nginxconf /etc/nginx/sites-available

Make a symbolic link into sites-enabled folder

	sudo ln -s /etc/nginx/sites-available/HomeAutomation /etc/nginx/sites-enabled

Verify that apache2-utils are installed.
    	
	sudo apt-get install apache2-utils

Create a password file and a first user
    
	sudo htpasswd -c /etc/apache2/.htpasswd user1
        
In the same way create other user-password pairs without -c flag

Install Adafruit DHT library

	git clone https://github.com/adafruit/Adafruit_Python_DHT.git
	cd Adafruit_Python_DH
	sudo apt-get install build-essential python-dev python-openssl
	sudo python setup.py install

Install bluetooth handler

	sudo apt-get install libbluetooth-dev
	sudo pip install pybluez


