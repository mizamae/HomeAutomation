import json
from django.utils import timezone

class NotificationManager(object):
    
    @staticmethod
    def getUsers():
        from authtools.models import User
        return User.objects.filter(profile__notifications=True)
        
    @staticmethod
    def send_web_push(users, title, message_body,timestamp=None,tag=None,url=None):
        if timestamp==None:
            timestamp=timezone.now().strftime('%d/%m/%Y %H:%M:%S')
        else:
            timestamp=timestamp.strftime('%d/%m/%Y %H:%M:%S')
            
        try:
            for user in users:
                if user.profile.notifications and user.profile.subscription_token!="":
                    from pywebpush import webpush, WebPushException
                    from django.conf import settings
                    
                    if not isinstance(user.profile.subscription_token,dict):
                        import ast
                        token=ast.literal_eval(user.profile.subscription_token)
                    else:
                        token=user.profile.subscription_token
                        
                    VAPID_PRIVATE_KEY = open(settings.WEBPUSH_SETTINGS["VAPID_PRIVATE_KEY_PATH"], "r+").readline().strip("\n")
                    webpush(
                        subscription_info=token,
                        data=json.dumps({'body':message_body,'title':title,'timestamp':timestamp,'tag':tag,'url':url}),
                        vapid_private_key=VAPID_PRIVATE_KEY,
                        vapid_claims={"sub":"mailto:"+settings.WEBPUSH_SETTINGS["VAPID_ADMIN_EMAIL"]},
                    )
        except WebPushException as ex:
            print("I'm sorry honey, but I can't do that: {}", repr(ex))
            # Mozilla returns additional information in the body of the response.
            if ex.response and ex.response.json():
                extra = ex.response.json()
                print("Remote service replied with a {}:{}, {}",
                      extra.code,
                      extra.errno,
                      extra.message
                      )