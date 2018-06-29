import os
from subprocess import Popen, PIPE
from EventsAPP.consumers import PublishEvent

class NginxManager(object):
    
    def restart(self):
        cmd='sudo systemctl restart nginx'
        os.system(cmd)
        PublishEvent(Severity=0,Text='Nginx restarted OK',Persistent=True,Code='Nginx-0')
    
    def reload(self):
        cmd='sudo nginx -s reload'
        os.system(cmd)
        PublishEvent(Severity=0,Text='Nginx configuration reloaded OK',Persistent=True,Code='Nginx-0')
        
    def createUser(self,user,passw,firstUser=False):
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
    
    def blockIP(self,IP):
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
        PublishEvent(Severity=1,Text='IP address '+IP+ ' has been blocked',Persistent=True,Code='Nginx-'+IP)
            
    @staticmethod
    def editConfigFile(key,delimiter,newValue,endChar=';'):
        from MainAPP.constants import NGINX_CONF_PATH
        try:
            file = open(NGINX_CONF_PATH, 'r') 
        except:
            text=_('Error opening the file ') + NGINX_CONF_PATH
            PublishEvent(Severity=2,Text=text,Persistent=True,Code='FileIOError-0')
        
        lines=file.readlines()
        if len(lines)>0:
            keyFound=False
            for i,line in enumerate(lines):
                if key in line:
                    keyFound=True
                    values=line.split(delimiter)
                    lines[i]=values[0]+delimiter+newValue+endChar+delimiter+key+'\n'
            if keyFound:
                fileString=''.join(lines)
                file.close()
                from subprocess import Popen, PIPE
                cmd="echo '"+fileString+"' | sudo tee "+ NGINX_CONF_PATH
                process = Popen(cmd, shell=True,
                            stdout=PIPE,stdin=PIPE, stderr=PIPE,universal_newlines=True)
                stdout, err = process.communicate()
