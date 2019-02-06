// When we're using HTTPS, use WSS too.
var ws_scheme = window.location.protocol == "https:" ? "wss" : "ws";
var Eventsocket = new WebSocket(ws_scheme + '://' + window.location.host + "/stream/Events/");
var webSocketEventsBridge = new channels.WebSocketBridge();
webSocketEventsBridge.connect(ws_scheme + '://' + window.location.host + "/stream/Events/");
webSocketEventsBridge.listen();
var EVTstable=document.getElementById("eventsTable");
var EVTstableContainer=document.getElementById("eventsContainer");

$(function()
{
    checkEventsVisibility();
    Eventsocket.onmessage = function(message) {
                var event = JSON.parse(message.data);
                if (event!=null)
                {
                	if (event.pk==null){updateEvent(event);}
                }
            };
    webSocketEventsBridge.demultiplex('Event_critical', function(payload, streamName) 
    {
                // Handle different actions
                if (payload.action == "create") 
                {
                    showEvent(payload.data)
                    console.log("New Events model created : " + payload.data.Text);
                }
                if (payload.action == "update")
                {
                    updateEvent(payload.data)  
                }
                if (payload.action == "delete")
                {
                    deleteEvent(payload.data)  
                }
    });
    // Helpful debugging
    webSocketEventsBridge.socket.addEventListener('open', 
        function() { 
            console.log("Connected to Events socket"); 
            label=document.getElementById('RT_status');
            if (label.innerHTML=="Disconnected from Events engine")
            {label.innerHTML="";}
    });
    webSocketEventsBridge.socket.addEventListener('close', 
        function() { 
            console.log("Disconnected to Events socket"); 
            label=document.getElementById('RT_status');
            label.style.color="Red";
            label.innerHTML="Disconnected from Events engine";
    });
});

function checkEventsVisibility()
{
    if (EVTstable.rows.length>=2)
    {
        EVTstableContainer.className=EVTstableContainer.className.replace('hidden','');
    }else
    {
        if (EVTstableContainer.className.indexOf("hidden")<0)
        {EVTstableContainer.className=EVTstableContainer.className +' hidden';}
    }
    
}
function acknowledge(pk,code)
{
    if (pk)
    {
        webSocketEventsBridge.stream('Event_ack').send({
            "pk": pk,
            "action": "delete",
            "data": {}
        });
    }else
    {
    	event={};
    	event.Code=code;
        deleteEvent(event);
    }
}
function deleteEvent(event)
{
    EVTstableContainer.className=EVTstableContainer.className.replace('hidden','');
    var rownum=-1;
    for (var i = 0, row; row = EVTstable.rows[i]; i++) {
        if ((row.cells[0].innerHTML==event.Code))
        {
            EVTstable.deleteRow(i);
            break;
        }
    }
    checkEventsVisibility();
}
function updateEvent(event)
{
    EVTstableContainer.className=EVTstableContainer.className.replace('hidden','');
    var rownum=-1;
    for (var i = 0, row; row = EVTstable.rows[i]; i++) {
        if ((row.cells[0].innerHTML==event.Code))
        {
            rownum=i;
            break;
        }
    }
    if (rownum>=1)
    {
        var offset = new Date().getTimezoneOffset();
        var d = new Date(event.Timestamp);
        row.cells[1].innerHTML=d.toLocaleString()+ ' *';
        row.cells[2].innerHTML=event.Severity;
        row.cells[3].innerHTML=event.Text;
        if (event.Severity < 2)
		{row.className="alert-narrow alert-info";}
        else if (event.Severity < 4)
		{row.className="alert-narrow alert-warning";} 
		else
		{row.className="alert-narrow alert-danger"}
    }else
    {showEvent(event);}
    
}
    
function showEvent(event)
{
    if (event.Timestamp)
    {
        EVTstableContainer.className=EVTstableContainer.className.replace('hidden','');
        var row = EVTstable.insertRow(-1);
        if (event.Severity<2){row.className="alert-narrow alert-info";}
        else if (event.Severity<4){row.className="alert-narrow alert-warning";}
        else {row.className="alert-narrow alert-danger";}
        var cell0 = row.insertCell(0);
        cell0.className="hidden";
        var cell1 = row.insertCell(1);
        cell1.className="hidden-sm hidden-xs";
        var cell2 = row.insertCell(2);
        cell2.className="hidden-sm hidden-xs";
        var cell3 = row.insertCell(3);
        var cell4 = row.insertCell(4);
        var offset = new Date().getTimezoneOffset();
        var d = new Date(event.Timestamp);
        cell0.innerHTML=event.Code;
        row.appendChild(cell0);
        cell1.innerHTML=d.toLocaleString();
        row.appendChild(cell1);
        cell2.innerHTML=event.Severity;
        row.appendChild(cell2);
        cell3.innerHTML=event.Text;
        row.appendChild(cell3);
        var buttonDel=document.createElement('a');
        buttonDel.className="btn btn-default btn-xs";
        buttonDel.role="button";
        buttonDel.id="delete"+(EVTstable.rows.length-1).toString();
        buttonDel.addEventListener("click", function(){ acknowledge(event.pk,event.Code); });
        buttonDel.innerHTML="OK";
        cell4.appendChild(buttonDel);
        row.appendChild(cell4);
        checkEventsVisibility();
    }
}
