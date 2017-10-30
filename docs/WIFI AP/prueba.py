import subprocess
import time
proc = subprocess.run(args=['sudo','service','hostapd','status'],stdout=subprocess.PIPE)
print(proc)

if proc.returncode==0:
    print("Execution OK")
else:
    print("Error " + str(proc.returncode))

time.sleep(1)
print("Finished")