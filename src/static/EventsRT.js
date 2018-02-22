// When we're using HTTPS, use WSS too.
var ws_scheme = window.location.protocol == "https:" ? "wss" : "ws";
var socket = new WebSocket(ws_scheme + '://' + window.location.host + "/stream/Events/");
var webSocketEventsBridge = new channels.WebSocketBridge();
webSocketEventsBridge.connect(ws_scheme + '://' + window.location.host + "/stream/Events/");
webSocketEventsBridge.listen();
var EVTstable=document.getElementById("eventsTable");
var EVTstableContainer=document.getElementById("eventsContainer");

$(function()
{
    checkEventsVisibility();
    socket.onmessage = function(message) {
                var data = JSON.parse(message.data);
                showEvent(data)
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
            {label.innerHTML=='';}
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
function acknowledge(pk,add=null)
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
        var data={};
        data.Text=add;
        deleteEvent(data);
    }
}
function deleteEvent(data)
{
    EVTstableContainer.className=EVTstableContainer.className.replace('hidden','');
    var rownum=-1;
    for (var i = 0, row; row = EVTstable.rows[i]; i++) {
        if ((row.cells[2].innerHTML==data.Text))
        {
            EVTstable.deleteRow(i);
            break;
        }
    }
    checkEventsVisibility();
}
function updateEvent(data)
{
    EVTstableContainer.className=EVTstableContainer.className.replace('hidden','');
    var rownum=-1;
    for (var i = 0, row; row = EVTstable.rows[i]; i++) {
        if ((row.cells[2].innerHTML==data.Text))
        {
            rownum=i;
            break;
        }
    }
    if (rownum>1)
    {
        var offset = new Date().getTimezoneOffset();
        var d = new Date(data.Timestamp);
        row.cells[0].innerHTML=d.toLocaleString()+ ' *';
    }
    
}
    
function showEvent(data)
{
    if (data.Timestamp)
    {
        EVTstableContainer.className=EVTstableContainer.className.replace('hidden','');
        var row = EVTstable.insertRow(-1);
        if (data.Severity<2){row.className="alert-narrow alert-info";}
        else if (data.Severity<4){row.className="alert-narrow alert-warning";}
        else {row.className="alert-narrow alert-danger";}
        var cell1 = row.insertCell(0);
        cell1.className="hidden-sm hidden-xs";
        var cell2 = row.insertCell(1);
        cell2.className="hidden-sm hidden-xs";
        var cell3 = row.insertCell(2);
        var cell4 = row.insertCell(3);
        var offset = new Date().getTimezoneOffset();
        var d = new Date(data.Timestamp);
        cell1.innerHTML=d.toLocaleString();
        row.appendChild(cell1);
        cell2.innerHTML=data.Severity;
        row.appendChild(cell2);
        cell3.innerHTML=data.Text;
        row.appendChild(cell3);
        var buttonDel=document.createElement('a');
        buttonDel.className="btn btn-default btn-xs";
        buttonDel.role="button";
        buttonDel.id="delete"+(EVTstable.rows.length-1).toString();
        buttonDel.addEventListener("click", function(){ acknowledge(data.pk,data.Text); });
        buttonDel.innerHTML="OK";
        cell4.appendChild(buttonDel);
        row.appendChild(cell4);
        checkEventsVisibility();
    }
}
