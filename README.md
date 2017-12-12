

# HomeAutomation

HomeAutomation is a web application that basically pretends to implement a simple and affordable, yet powerful, data acquisition environment based on open-hardware platforms such as [Arduino][0] and [Raspberry Pi][1]. 
It is built with [Python][2] using the [Django Web Framework][3].

The project consist of a Master unit (usually a Raspberry) that is in charge of controlling everything. Around it, several Slave devices (usually Arduinos) will be waiting for an HTTP query from the Master unit. When a proper query reaches an Slave device, it responds with an XML datagram containing the requested information. The Master unit stores the information in a database and this is all, simple isn't it??

The communication between the Master and the Slaves will be defined in the <b>Datagrams model</b>. The information sent by the Slaves is contained within a so called <b>datagram</b>. Each Slave may have more than one datagram with different information, sampling times, etc.

This project has the following basic apps:

* HomeAutomation: this one is the core application of the project. It contains all the configuration parameters, the views, routing, urls, etc.
* Devices: this app contains all the basic functions that are shared by any kind of devices that can be connected to the environment.
* LocalDevices: this application handles and configures the devices that are directly connected to the main unit such as DHT sensors
* RemoteDevices: handles the devices that are connected to the main unit by means of a HTTP connection.
* Master_GPIOs: handles the status and operations of the main device local GPIOs.

## Learning objectives

Eventhough it may seem that the main objective of this project is to gather information about habits, daily patterns, etc, actually it is not. The main and initial objective of the project was diving into Python. One thing took to another and finally this project was raised. If one decides to accept the challenge of getting involved in this project (as a developer or a power-user), he/she will gain expertise and knowledge in the follwoing fields:

* Programming in Python (40%)
* Programming in JavaScript (20%)
* Programming HTML & CSS (30%)
* Hints on Linux OS
* Programming C++ for Arduino (10%)

## Project roadmap

This project started in May 2017 and it never expects to be finished since a continuous development phylosophy is laying behind it. Eventhough it is an open-source and open-hardware project, it is being carefully developed and tested following industrial procedures that hopefully will end up in a robust and stable first release.

The minimum features required for the very first release are:

* Fully operational device detection and configuration (via Web interface).
* Fully operational device interrogation and data storage (using SQLite DB).
* Web interface to view data from devices.

and its target deadline is set by end 2017. By this date, an operating environment consisting of a Master unit and at least one Slave device should be up and running.

## Installation

If you just want to use the application and have no interest on developing, you should be installing the Raspbian image provided at ...

### Quick start


Install all dependencies:

	pip install -r requirements.txt

Install gunicorn:
	
	sudo pip3 install gunicorn

Run migrations:

	python manage.py makemigrations --fake
	python manage.py migrate

### Detailed instructions

Take a look at the docs for more information.

[0]: https://www.arduino.cc/
[1]: https://www.raspberrypi.org/
[2]: https://www.python.org/
[3]: https://www.djangoproject.com/

