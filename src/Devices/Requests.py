import Devices.models
   
def initialize_polling_devices():
    DVs=Devices.models.DeviceModel.objects.all()
    if DVs is not None:
        for DV in DVs:
            DV.update_requests()


                    

       

    

    