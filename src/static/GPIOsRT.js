// When we're using HTTPS, use WSS too.
var ws_scheme = window.location.protocol == "https:" ? "wss" : "ws";

var webSocketGPIOBridge = new channels.WebSocketBridge();
webSocketGPIOBridge.connect(ws_scheme + '://' + window.location.host + "/stream/DevicesAPP/");
webSocketGPIOBridge.listen();
var GPIOstable=document.getElementById("gpiosTable");
var GPIOstableContainer=document.getElementById("gpiosContainer");


$(function () {
    
	webSocketGPIOBridge.demultiplex('GPIO_values', function(payload, streamName) {
        // Handle different actions
        if (payload.action == "create") {
            // Create the new GPIO model
			add_GPIO(payload.pk,payload.data)
            console.log("New IO model created");
        } else if (payload.action == "update") {
			update_GPIO(payload.pk,payload.data.Label,payload.data.Value)
            console.log("Port ["+ String(payload.pk) + "] has changed to "+ payload.data.Value);
        } else if (payload.action == "delete") {
			delete_GPIO(parseInt(payload.pk))
        	console.log("IO model deleted");
        } else {
            console.log("Unknown action " + payload.action);
        }
    });

    // Helpful debugging
	webSocketGPIOBridge.socket.addEventListener('open', 
        function() { 
            console.log("Connected to GPIOs socket"); 
            label=document.getElementById('RT_status');
            if (label.innerHTML=="Disconnected from GPIOs engine")
            {label.innerHTML=='';}
    });
	webSocketGPIOBridge.socket.addEventListener('close', 
        function() { 
            console.log("Disconnected to GPIOs socket"); 
            label=document.getElementById('RT_status');
            label.style.color="Red";
            label.innerHTML="Disconnected from GPIOs engine"
    });
});

function add_GPIO(pin,data){
	var row = GPIOstable.insertRow(-1);
	var cell0 = row.insertCell(0);
	var cell1 = row.insertCell(1);
	var cell2 = row.insertCell(2);
	var cell3 = row.insertCell(3);
	cell0.innerHTML=pin;
	cell1.innerHTML=data.Label;
	row.appendChild(cell1);
	if (data.Value==1)
	{cell2.innerHTML='ON';}
	else{cell2.innerHTML='OFF';}
	row.appendChild(cell2);
}

function toggle_GPIO(pin) {

	webSocketGPIOBridge.stream('GPIO_update').send({
			"pk": pin,
			"action": "update",
			"data": {
				"value": null}
	});
}

function update_GPIO(pin,label,value){
	var rownum=-1;
	for (var i = 0, row; row = GPIOstable.rows[i]; i++) {
		if (parseInt(row.cells[0].innerHTML)==pin)
		{
			rownum=i;
			break;
		}
	}
	if (rownum>0)
	{
		var row=GPIOstable.rows[rownum];
		if (typeof label != "undefined") {row.cells[1].innerHTML=label;}
		if (typeof value != "undefined") {row.cells[2].innerHTML=(value==false ? "OFF":"ON")}
	}
}

function delete_GPIO(pin) {
	for (var i = 0, row; row = GPIOstable.rows[i]; i++) {
		if (parseInt(row.cells[0].innerHTML)==pin)
		{
			GPIOstable.deleteRow(i);
			break;
		}
	}        
}