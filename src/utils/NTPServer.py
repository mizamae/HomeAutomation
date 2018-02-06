import os

def restart():
    os.system("sudo /etc/init.d/ntp stop")
    os.system("sudo ntpd -q -g")
    os.system("sudo /etc/init.d/ntp start")