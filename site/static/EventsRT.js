// When we're using HTTPS, use WSS too.
var ws_scheme = window.location.protocol == "https:" ? "wss" : "ws";
var socket = new WebSocket(ws_scheme + '://' + window.location.host + "/stream/Events/");
var webSocketBridge = new channels.WebSocketBridge();
webSocketBridge.connect(ws_scheme + '://' + window.location.host + "/stream/Events/");
webSocketBridge.listen();
        
$(function()
{
    checkEventsVisibility();
    socket.onmessage = function(message) {
                var data = JSON.parse(message.data);
                showEvent(data)
            };
    webSocketBridge.demultiplex('Event_critical', function(payload, streamName) 
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
    socket.addEventListener('open', 
        function() { 
            console.log("Connected to notification socket"); 
            label=document.getElementById('RT_status');
            label.style.color="LimeGreen";
            label.innerHTML="Connected to Events engine"
    });
    socket.addEventListener('close', 
        function() { 
            console.log("Disconnected to notification socket"); 
            label=document.getElementById('RT_status');
            label.style.color="Red";
            label.innerHTML="Disconnected from Events engine"
    });
});

function checkEventsVisibility()
{
    var table=document.getElementById("eventsTable");
    var container=document.getElementById("eventsContainer");
    if (table.rows.length>=2)
    {
        container.className=container.className.replace('hidden','');
    }else
    {
        if (container.className.indexOf("hidden")<0)
        {container.className=container.className +' hidden';}
    }
    
}
function acknowledge(pk,add=null)
{
    if (pk)
    {
        webSocketBridge.stream('Event_ack').send({
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
    var container=document.getElementById("eventsContainer");
    container.className=container.className.replace('hidden','');
    var table=document.getElementById("eventsTable");
    var rownum=-1;
    for (var i = 0, row; row = table.rows[i]; i++) {
        if ((row.cells[2].innerHTML==data.Text))
        {
            table.deleteRow(i);
            break;
        }
    }
    checkEventsVisibility();
}
function updateEvent(data)
{
    var container=document.getElementById("eventsContainer");
    container.className=container.className.replace('hidden','');
    var table=document.getElementById("eventsTable");
    var rownum=-1;
    for (var i = 0, row; row = table.rows[i]; i++) {
        if ((row.cells[2].innerHTML==data.Text))
        {
            rownum=i;
            break;
        }
    }
    if (rownum>1)
    {
        row.cells[0].innerHTML=data.Timestamp + ' *';
    }
    
}
    
function showEvent(data)
{
    if (data.Timestamp)
    {
        var container=document.getElementById("eventsContainer");
        container.className=container.className.replace('hidden','');
        var table=document.getElementById("eventsTable");
        var row = table.insertRow(-1);
        if (data.Severity<2){row.className="alert-narrow alert-info";}
        else if (data.Severity<4){row.className="alert-narrow alert-warning";}
        else {row.className="alert-narrow alert-danger";}
        var cell1 = row.insertCell(0);
        var cell2 = row.insertCell(1);
        var cell3 = row.insertCell(2);
        var cell4 = row.insertCell(3);
        cell1.innerHTML=data.Timestamp;
        row.appendChild(cell1);
        cell2.innerHTML=data.Severity;
        row.appendChild(cell2);
        cell3.innerHTML=data.Text;
        row.appendChild(cell3);
        var buttonDel=document.createElement('a');
        buttonDel.className="btn btn-default btn-xs";
        buttonDel.role="button";
        buttonDel.id="delete"+(table.rows.length-1).toString();
        buttonDel.addEventListener("click", function(){ acknowledge(data.pk,data.Text); });
        buttonDel.innerHTML="OK";
        cell4.appendChild(buttonDel);
        row.appendChild(cell4);
        checkEventsVisibility();
    }
}
