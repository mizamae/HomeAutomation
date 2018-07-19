https://learn.adafruit.com/setting-up-a-raspberry-pi-as-a-wifi-access-point/install-software

	sudo apt-get install hostapd

SETUP WLAN0 FOR STATIC IP

	sudo nano /etc/network/interfaces

file should look like: 

	# interfaces(5) file used by ifup(8) and ifdown(8)

	# Please note that this file is written to be used with dhcpcd
	# For static IP, consult /etc/dhcpcd.conf and 'man dhcpcd.conf'
	
	# Include files from /etc/network/interfaces.d:
	source-directory /etc/network/interfaces.d
	auto lo
	iface lo inet loopback
		
	# Ideally eth0 should be set as static IP. It can be done in the router though
	auto eth0
		iface eth0 inet static
		address 192.168.0.160
		netmask 255.255.255.0
		gateway 192.168.0.1
		network 192.168.0.0
		
	auto wlan0
		allow-hotplug wlan0
		iface wlan0 inet static
		address 10.10.10.1
		netmask 255.255.255.0
		gateway 10.10.10.1
		network 10.10.10.0
		
	allow-hotplug wlan1
	iface wlan1 inet manual
		 wpa-conf /etc/wpa_supplicant/wpa_supplicant.conf

    
CONFIGURE ACCESS POINT

	sudo nano /etc/hostapd/hostapd.conf

write:

	interface=wlan0
	#driver=rtl871xdrv #commented if using rasppi 3 built-in adapter
	ssid=Pi_AP
	country_code=ES
	hw_mode=g
	channel=6
	macaddr_acl=0
	auth_algs=1
	ignore_broadcast_ssid=0 # set this to 1 to hide the ssid
	wpa=2
	wpa_passphrase=Raspberry
	wpa_key_mgmt=WPA-PSK
	wpa_pairwise=CCMP
	wpa_group_rekey=86400
	ieee80211n=1
	wme_enabled=1

Then execute edit hostapd default config

	sudo nano /etc/default/hostapd

Find the line #DAEMON_CONF="" and edit it so it says DAEMON_CONF="/etc/hostapd/hostapd.conf"

- sudo nano /etc/init.d/hostapd
Find the line DAEMON_CONF= and change it to DAEMON_CONF=/etc/hostapd/hostapd.conf

FIRST TEST
- sudo /usr/sbin/hostapd /etc/hostapd/hostapd.conf

FINISHING UP
now that we know it works, time to set it up as a 'daemon' - a program that will start when the Pi boots.
- sudo service hostapd start 
you can  check the status of the host AP server with
- sudo service hostapd status
stop the service 

	sudo service hostapd stop 

To start the daemon services. Verify that they both start successfully (no 'failure' or 'errors')
Then to make it so it runs every time on boot
- sudo update-rc.d hostapd enable