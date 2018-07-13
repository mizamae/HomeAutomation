import pyrebase

class FireBaseWrapper(object):
    config = {
        'apiKey': "AIzaSyAsBHkAPSyPO129BYAq30HV_nSUYgmlosM",
        'authDomain': "diy4dot0-homeautomation.firebaseapp.com",
        'databaseURL': "https://diy4dot0-homeautomation.firebaseio.com",
        'projectId': "diy4dot0-homeautomation",
        'storageBucket': "diy4dot0-homeautomation.appspot.com",
        'messagingSenderId': "219709098290",
        #"serviceAccount": "diy4dot0-homeautomation-firebase-adminsdk-xn9dg-2dce53e030.json"
      }

    def __init__(self):
        self.firebase = pyrebase.initialize_app(self.config)
        self.db = self.firebase.database()
        self.auth = self.firebase.auth()
        
    def createUser(self,email,passw):
        try:
            user = self.auth.create_user_with_email_and_password(email,passw)
            return user
        except:
            return None
    
    def authenticateUser(self,email,passw):
        try:
            user = self.auth.sign_in_with_email_and_password(email,passw)
            return user
        except:
            return None
    
# import firebase_admin
# from firebase_admin import credentials
# 
# cred = credentials.Certificate("diy4dot0-homeautomation-firebase-adminsdk-xn9dg-2dce53e030.json")
# firebase_admin.initialize_app(cred)

def main():
    instance=FireBaseWrapper()
    user=instance.authenticateUser(email='mizamae@gmail.com',passw='valtierra')
    print(user)
    

        
if __name__ == '__main__':
    main()
