// When we're using HTTPS, use WSS too.
var ws_scheme = window.location.protocol == "https:" ? "wss" : "ws";
var webSocketDevicesBridge = new channels.WebSocketBridge();
webSocketDevicesBridge.connect(ws_scheme + '://' + window.location.host + "/stream/DevicesAPP/");
webSocketDevicesBridge.listen();
var DVstable=document.getElementById("devicesTable");

$(function()
{
    webSocketDevicesBridge.demultiplex('Device_params', function(payload, streamName) 
    {
                // Handle different actions
                if (payload.action == "create") 
                {
                    console.log("New Device model created : " + payload.data.Name);
                }
                if (payload.action == "update")
                {
                	update_Device(payload.data); 
                }
                if (payload.action == "delete")
                {
                	console.log("Device model deleted : " + payload.data.Name);
                }
    });
    // Helpful debugging
    webSocketEventsBridge.socket.addEventListener('open', 
        function() { 
            console.log("Connected to Devices socket"); 
            label=document.getElementById('RT_status');
            if (label.innerHTML=="Disconnected from Devices engine")
            {label.innerHTML=='';}
    });
    webSocketEventsBridge.socket.addEventListener('close', 
        function() { 
            console.log("Disconnected to Devices socket"); 
            label=document.getElementById('RT_status');
            label.style.color="Red";
            label.innerHTML="Disconnected from Devices engine";
    });
});

function update_Device(device){

	var rownum=-1;
    for (var i = 0, row; row = DVstable.rows[i]; i++) {
        if ((row.cells[0].innerHTML==device.Name))
        {
            rownum=i;
            break;
        }
    }
    if (rownum>=1)
    {
        var offset = new Date().getTimezoneOffset();
        var d = new Date(device.LastUpdated);
        row.cells[3].innerHTML=d.toLocaleString()+ ' *';
        if (device.State == 0)
		{row.cells[2].style.backgroundColor= "#FF0000";
		row.cells[2].innerHTML="STOPPED";
		}
        else
		{row.cells[2].style.backgroundColor= "#00FF00";
		row.cells[2].innerHTML="RUNNING";
		} 
    }
}
