from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import os
# GOOGLE DRIVE FOLDERS
DRIVE_ROOT_FOLDER='DIY4dot0'
DRIVE_DJANGO_FOLDER='DjangoDB'
DRIVE_REGISTERS_FOLDER='RegistersDB'
# LOCAL FOLDERS
from MainAPP.constants import DJANGO_DB_PATH,REGISTERS_DB_PATH
from django.utils import timezone
REGISTERS_DB_PATH=REGISTERS_DB_PATH.replace("_XYEARX_",str(timezone.now().year))
CLIENT_SECRETS_ROOT=os.path.abspath(os.path.dirname(__file__))
GoogleAuth.DEFAULT_SETTINGS['save_credentials'] = False
GoogleAuth.DEFAULT_SETTINGS['client_config_file'] = os.path.join(CLIENT_SECRETS_ROOT,'client_secrets.json')

class GoogleDriveWrapper(object):
    __authorized=False
    
    def __init__(self):
        self.drive=None
        self.gauth = GoogleAuth()
        self.AUTH_URL=self.gauth.GetAuthUrl()
            
    def checkCredentials(self):
        # Try to load saved client credentials
        self.gauth.LoadCredentialsFile(os.path.join(CLIENT_SECRETS_ROOT,"GDriveCreds.json"))
        if self.gauth.credentials is None:
            return False
        elif self.gauth.access_token_expired:
            # Refresh them if expired
            self.gauth.Refresh()
        else:
            # Initialize the saved creds
            self.gauth.Authorize()
        self.drive = GoogleDrive(self.gauth)
        self.checkDriveFolders()
        self.__authorized=True
        return True
            
    def saveCredentials(self):
        # Save the current credentials to a file
        self.gauth.SaveCredentialsFile(os.path.join(CLIENT_SECRETS_ROOT,"GDriveCreds.json"))
        
    def checkDriveFolders(self):
        # ROOT
        folder=self.checkItemExist(title=DRIVE_ROOT_FOLDER)
        if folder==None:
            #Create ROOT folder
            folder_metadata = {'title' : DRIVE_ROOT_FOLDER, 'mimeType' : 'application/vnd.google-apps.folder'}
            folder = self.drive.CreateFile(folder_metadata)
            folder.Upload()
        self.RootFolderID=folder['id']
        # DJANGO DB
        folder=self.checkItemExist(title=DRIVE_DJANGO_FOLDER,root=self.RootFolderID)
        if folder==None:
            #Create Django folder
            folder_metadata = {'title' : DRIVE_DJANGO_FOLDER, 'mimeType' : 'application/vnd.google-apps.folder',"parents": [{"kind": "drive#fileLink", "id": self.RootFolderID}]}
            folder = self.drive.CreateFile(folder_metadata)
            folder.Upload()
        self.DjangoFolderID=folder['id']
        # REGISTERS DB
        folder=self.checkItemExist(title=DRIVE_REGISTERS_FOLDER,root=self.RootFolderID)
        if folder==None:
            #Create Registers folder
            folder_metadata = {'title' : DRIVE_REGISTERS_FOLDER, 'mimeType' : 'application/vnd.google-apps.folder',"parents": [{"kind": "drive#fileLink", "id": self.RootFolderID}]}
            folder = self.drive.CreateFile(folder_metadata)
            folder.Upload()
        self.RegistersFolderID=folder['id']
        
    def checkItemExist(self,title,root='root'):
        file_list = self.drive.ListFile({'q': "'"+root+"' in parents and trashed=false"}).GetList()
        for item in file_list:
            if item['title'] == title:
                return item
        return None
    
    def uploadFile(self,title,sourcepath,folderid):
        file = self.drive.CreateFile({'title': title,"parents": [{"kind": "drive#fileLink", "id": folderid}]})
        file.SetContentFile(sourcepath)
        file.Upload() # Files.insert()
    
    def uploadDBs(self):
        self.uploadFile(title='DjangoDB_'+str(timezone.now().month)+'-'+str(timezone.now().year)+'.sqlite3', sourcepath=DJANGO_DB_PATH, folderid=self.DjangoFolderID)
        self.uploadFile(title='RegistersDB_'+str(timezone.now().month)+'-'+str(timezone.now().year)+'.sqlite3', sourcepath=REGISTERS_DB_PATH, folderid=self.RegistersFolderID)


