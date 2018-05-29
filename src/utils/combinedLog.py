
class CombinedLogParser(object):
    '''
    Parses a log file formatted following Combined log format as per http://httpd.apache.org/docs/current/logs.html#combined
    '''
    StatusCodes={'400':'Bad Request',
                 '401':'Unauthorized',
                 '403':'Forbidden',
                 '404':'Not Found',
                 '405':'Method not Allowed',
                 '408':'Request Timeout',
                 '429':'Too Many Requests',
                 '444':'No Response',
                 '495':'SSL Certificate Error',
                 '499':'Client Closed Request',
                 }
    def __init__(self,path='/var/log/nginx/access.log'):
        self.path=path
        pass
    
    def getNginxAccessHTTPCodes(self,hours=24):
        from subprocess import Popen, PIPE
        # GETS THE NUMBER OF TIMES EACH HTTP RESPONSE CODE HAS HAPPENED in the last 24 hours
        process = Popen("awk -vDate=`date -d'now-"+str(hours)+" hours' +[%d/%b/%Y:%H:%M:%S` ' { if ($4 > Date) {print $9}}' "+self.path+" | sort | uniq -c | sort -rn", shell=True,
                        stdout=PIPE, stderr=PIPE,universal_newlines=True)
        stdout, stderr = process.communicate()
        rows=stdout.split('\n')
        attempts={}
        for row in rows:
            cols=row.strip().split(' ')
            if cols[0].isnumeric() and cols[1].isnumeric():
                attempts[cols[1]]=int(cols[0])
        # attempts is a dictionary with the keys=HTTP response codes and the fields equal to the number of occurences
        return attempts
    
    def getNginxAccessIPs(self,hours=24,codemin=400):
        # GETS THE NUMBER OF TIMES EACH IP RECEIVED AN HTTP RESPONSE CODE GREATER THEN codemin in the last 24 hours
        from subprocess import Popen, PIPE
        process = Popen("awk -vDate=`date -d'now-"+str(hours)+" hours' +[%d/%b/%Y:%H:%M:%S` ' { if ($4 > Date && $9 >= "+str(codemin)+") {print $1}}' "+self.path+" | sort | uniq -c | sort -rn", shell=True,
                        stdout=PIPE, stderr=PIPE,universal_newlines=True)
        stdout, stderr = process.communicate()
        rows=stdout.split('\n')
        data= map(str.strip,rows)
        attempts=[]
        for i,row in enumerate(data):
            cols=row.split(' ')
            if cols[0].isnumeric():
                attempts.append({'IP':cols[1],'trials':int(cols[0])})
        return attempts

# instance=CombinedLogParser()
# print(instance.getNginxAccessHTTPCodes())
# for element in instance.getNginxAccessIPs(hours=24):
#     print(element)
