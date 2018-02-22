// When we're using HTTPS, use WSS too.
var ws_scheme = window.location.protocol == "https:" ? "wss" : "ws";
var webSocketAVARsBridge = new channels.WebSocketBridge();
webSocketAVARsBridge.connect(ws_scheme + '://' + window.location.host + "/stream/MainAPP/avars/");
webSocketAVARsBridge.listen();

var AVARstableContainer=document.getElementById("avarsContainer");
var AVARstable=document.getElementById("avarsTable");

$(function()
{
    checkEventsVisibility();
    webSocketAVARsBridge.socket.onmessage = function(message) {
                var data = JSON.parse(message.data);
                updateAvar(data)
            };
            
/*    webSocketAVARsBridge.demultiplex('AVAR_values', function(payload, streamName) 
    {
                // Handle different actions
                if (payload.action == "create") 
                {
                    showEvent(payload.data)
                    console.log("New AutomationVars model created : " + payload.data.Text);
                }
                if (payload.action == "update")
                {
                    updateEvent(payload.data)  
                }
                if (payload.action == "delete")
                {
                    deleteEvent(payload.data)  
                }
    });*/
    // Helpful debugging
    webSocketAVARsBridge.socket.addEventListener('open', 
        function() { 
            console.log("Connected to avars socket"); 
            label=document.getElementById('RT_status');
            if (label.innerHTML=="Disconnected from avars engine")
            {label.innerHTML=='';}
    });
    webSocketAVARsBridge.socket.addEventListener('close', 
        function() { 
            console.log("Disconnected to avars socket"); 
            label=document.getElementById('RT_status');
            label.style.color="Red";
            label.innerHTML="Disconnected from avars engine";
    });
});

function checkAvarsVisibility()
{
    if (AVARstable.rows.length>=2)
    {
        AVARstableContainer.className=AVARstableContainer.className.replace('hidden','');
    }else
    {
        if (AVARstableContainer.className.indexOf("hidden")<0)
        {AVARstableContainer.className=AVARstableContainer.className +' hidden';}
    }
    
}

function deleteAvar(data)
{
    AVARstableContainer.className=AVARstableContainer.className.replace('hidden','');
    var rownum=-1;
    for (var i = 0, row; row = AVARstable.rows[i]; i++) {
        if ((row.cells[2].innerHTML==data.Text))
        {
            AVARstable.deleteRow(i);
            break;
        }
    }
    checkEventsVisibility();
}
function updateAvar(data)
{
    AVARstableContainer.className=AVARstableContainer.className.replace('hidden','');
    var rownum=-1;
    for (var i = 0, row; row = AVARstable.rows[i]; i++) {
        if ((row.cells[0].innerHTML==data.Label))
        {
            rownum=i;
            break;
        }
    }
    if (rownum>=1)
    {
    	var valueSpan=row.querySelector("#value");
    	valueSpan.innerHTML=data.Value;
    	var timeSpan=row.querySelector("#timestamp");
    	var d = new Date(data.Timestamp);
    	timeSpan.innerHTML=d.toLocaleString();
    }
    
}
    
function showAvar(data)
{
    if (data.Label)
    {
        AVARstableContainer.className=AVARstableContainer.className.replace('hidden','');
        var row = AVARstable.insertRow(-1);
        if (data.Severity<2){row.className="alert-narrow alert-info";}
        else if (data.Severity<4){row.className="alert-narrow alert-warning";}
        else {row.className="alert-narrow alert-danger";}
        var cell1 = row.insertCell(0);
        var cell2 = row.insertCell(1);
        var cell3 = row.insertCell(2);
        var cell4 = row.insertCell(3);
        var offset = new Date().getTimezoneOffset();
        var d = new Date(data.Timestamp);
        cell1.innerHTML=d.toLocaleString()
        row.appendChild(cell1);
        cell2.innerHTML=data.Severity;
        row.appendChild(cell2);
        cell3.innerHTML=data.Text;
        row.appendChild(cell3);
        var buttonDel=document.createElement('a');
        buttonDel.className="btn btn-default btn-xs";
        buttonDel.role="button";
        buttonDel.id="delete"+(AVARstable.rows.length-1).toString();
        buttonDel.addEventListener("click", function(){ acknowledge(data.pk,data.Text); });
        buttonDel.innerHTML="OK";
        cell4.appendChild(buttonDel);
        row.appendChild(cell4);
        checkEventsVisibility();
    }
}
