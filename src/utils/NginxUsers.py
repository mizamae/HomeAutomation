from subprocess import Popen, PIPE
from EventsAPP.consumers import PublishEvent

def createUser(user,passw,firstUser=False):
    if firstUser:
        cmd='sudo htpasswd -ci /etc/apache2/.htpasswd '+user
    else:
        cmd='sudo htpasswd -i /etc/apache2/.htpasswd '+user
        
    process = Popen(cmd, shell=True,
                    stdout=PIPE,stdin=PIPE, stderr=PIPE,universal_newlines=True)
    stdout, err = process.communicate(input=passw)
    
    if not 'Updating' in err and not 'Adding' in err:
        PublishEvent(Severity=5,Text=err,Persistent=True,Code='Nginx-1')
    else:
        PublishEvent(Severity=0,Text=err,Persistent=False,Code='Nginx-1')