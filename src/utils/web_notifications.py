def send_web_push(subscription_information, message_body):
    try:
        from pywebpush import webpush, WebPushException
        from django.conf import settings
        print(subscription_information)
        VAPID_PRIVATE_KEY = open(settings.WEBPUSH_SETTINGS["VAPID_PRIVATE_KEY_PATH"], "r+").readline().strip("\n")
        webpush(
            subscription_info=subscription_information,
            data=message_body,
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