Welcome to HomeAutomation!
==============================

TOTESTS:
	- Test to delete a device from the DB in the page deviceList
	- Registers DB should be splitted from Devices's so that yearly a new Register's DB is created (to avoid huge DBs)

TODOs:
	- Comparison and update of Device's and Register's DB when new configuration.xml file is introduced.
    
sudo systemctl restart daphne gunicorn worker


SETUP THE TIMEZONE FOR THE RASPBERRY:
sudo dpkg-reconfigure tzdata
sudo service cron restart
