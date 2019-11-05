import os
from subprocess import Popen, PIPE
from EventsAPP.consumers import PublishEvent

class NginxManager(object):
    
    @staticmethod
    def restart():
        cmd='sudo systemctl restart nginx'
        os.system(cmd)
        PublishEvent(Severity=0,Text='Nginx restarted OK',Persistent=True,Code='Nginx-0')
    
    @staticmethod
    def reload():
        cmd='sudo nginx -s reload'
        os.system(cmd)
        PublishEvent(Severity=0,Text='Nginx configuration reloaded OK',Persistent=True,Code='Nginx-0')
    
    @staticmethod
    def createUser(user,passw,firstUser=False):
        from MainAPP.constants import APACHE_HTPASSWD_PATH
        if firstUser:
            cmd='sudo htpasswd -ci '+APACHE_HTPASSWD_PATH+' ' +user
        else:
            cmd='sudo htpasswd -i '+APACHE_HTPASSWD_PATH+' ' +user
            
        process = Popen(cmd, shell=True,
                        stdout=PIPE,stdin=PIPE, stderr=PIPE,universal_newlines=True)
        stdout, err = process.communicate(input=passw)
        
        if not 'Updating' in err and not 'Adding' in err:
            PublishEvent(Severity=5,Text=err,Persistent=True,Code='Nginx-1')
        else:
            PublishEvent(Severity=0,Text=err,Persistent=False,Code='Nginx-1')
    
    @staticmethod
    def blockIP(IP):
        check=IP.split('.')
        if len(check)!=4:
            PublishEvent(Severity=2,Text='The IP received is not properly formatted. IP= ' + IP,Persistent=True,Code='Nginx-2')
            return -1
        else:
            for num in check:
                if not num.isnumeric():
                    PublishEvent(Severity=2,Text='The IP received is not properly formatted. IP= ' + IP,Persistent=True,Code='Nginx-2')
                    return -1
                
        from MainAPP.constants import BLOCK_IPS_PATH
        cmd="echo 'deny "+IP+";' | sudo tee -a "+ BLOCK_IPS_PATH
        process = Popen(cmd, shell=True,
                    stdout=PIPE,stdin=PIPE, stderr=PIPE,universal_newlines=True)
        stdout, err = process.communicate()
        if err=='':
            PublishEvent(Severity=1,Text='IP address '+IP+ ' has been blocked',Persistent=True,Code='Nginx-'+IP)
        else:
            PublishEvent(Severity=3,Text='Error blocking IP '+IP+ '. Err: '+ err,Persistent=True,Code='Nginx-'+IP)
    
    @staticmethod
    def setProxyCredential(PROXY_CREDENTIALS):
        from MainAPP.constants import NGINX_CONF_PATH
        import fileinput
        import sys
        previous=''
        with fileinput.input(files=(NGINX_CONF_PATH,),inplace=True) as f:
            for line in f:
                if 'auth_basic "off"' in line and not ('/stream/' in previous):
                    if PROXY_CREDENTIALS:
                        sys.stdout.write(line.replace('auth_basic "off"','#auth_basic "off"'))
                        text='Modified NGINX proxy security to ON'
                    else:
                        sys.stdout.write(line.replace('#auth_basic "off"','auth_basic "off"'))
                        text='Modified NGINX proxy security to OFF'
                elif len(line.strip())>0:
                    sys.stdout.write(line)
                previous=line
        
        PublishEvent(Severity=0,Text=text,Persistent=True,Code='Nginx-Proxy')
        
    @staticmethod
    def editConfigFile(ETH_IP,SITE_DNS):
        from MainAPP.constants import NGINX_GENERIC_CONF_PATH,NGINX_CONF_PATH
        try:
            f1 = open(NGINX_GENERIC_CONF_PATH, 'r') 
            open(NGINX_CONF_PATH, 'w').close()  # deletes the contents
            f2 = open(NGINX_CONF_PATH, 'w')    
        except:
            text=_('Error opening the file ') + NGINX_CONF_PATH
            PublishEvent(Severity=2,Text=text,Persistent=True,Code='FileIOError-0')
            return
           
        for line in f1:
            f2.write(line.replace('SITE_DNS', SITE_DNS).replace('ETH_IP', ETH_IP))
            
        f1.close()
        f2.close()
        
        text='Modified NGINX field ETH_IP to ' + str(ETH_IP)
        PublishEvent(Severity=0,Text=text,Persistent=True,Code='Nginx-ETH_IP')
        text='Modified NGINX field SITE_DNS to ' + str(SITE_DNS)
        PublishEvent(Severity=0,Text=text,Persistent=True,Code='Nginx-SITE_DNS')
