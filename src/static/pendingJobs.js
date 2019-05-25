

function init (DGs) {
	var divDGs=document.getElementById("cmbDG");
	var iSel = document.createElement('select');
	iSel.id="DG_selection";
	divDGs.appendChild(iSel);
	DGs.forEach(function(DG)
	{
		var iOpt = document.createElement('option');
		iOpt.value=DG.pk;
		iOpt.innerHTML=DG.id;
		iSel.appendChild(iOpt);
	});
    webSocketBridge.demultiplex('Device_pendingjob', function(payload, streamName) {
        // Handle different actions
        var error=document.getElementById('error');
        var error_row=document.getElementById('error_row');
        if (payload.action == "confirmed") 
        {
        	setTimeout(function(){
        		location.reload(true);
        	}, 1500);
        	var today=new Date().toISOString().slice(0,10);
        	document.getElementById("datePicker").value= today;
        	$(error_row).removeClass("alert-warning");
        	$(error_row).addClass("alert-success");
        	error.innerHTML="DB updated OK";
        	
        }else if (payload.action == "not confirmed") 
        {
        	description=payload.error;
        	$(error_row).addClass("alert-warning");
        	$(error_row).removeClass("alert-success");
        	error.innerHTML="Something failed: " + description;
        }
        else {
            console.log("Unknown action " + payload.action);
        }
    });
    // Helpful debugging
    webSocketBridge.socket.addEventListener('open', 
        function() { 
            console.log("Connected to notification socket"); 
            label=document.getElementById('RT_status');
            label.style.color="LimeGreen";
            label.innerHTML="Connected to RT engine"
    });
    webSocketBridge.socket.addEventListener('close', 
        function() { 
            console.log("Disconnected to notification socket"); 
            label=document.getElementById('RT_status');
            label.style.color="Red";
            label.innerHTML="Disconnected from RT engine"
    });
}


function sendPJOB(DV_pk,date,datagram)
{
	document.getElementById('error').innerHTML="";
	webSocketBridge.stream('Device_pendingjob').send({
        "pk": DV_pk,
        "action": "execute",
        "data": {"date":date,"DG_id":datagram}
    });     	
}

function insertPending(DV_pk)
{
	document.getElementById('error').innerHTML="";
    var date=document.getElementById("datePicker").value;
	var DG_pk=document.getElementById("DG_selection").value;
	webSocketBridge.stream('Device_pendingjob').send({
        "pk": DV_pk,
        "action": "add",
        "data": {"date":date,"DG_pk":DG_pk}
    });     	
}