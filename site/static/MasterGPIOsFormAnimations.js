var rows = document.getElementsByClassName("row");
var i;
var fieldNotificationTrue,fieldNotificationFalse;
var rowfieldLabelTrue,rowfieldLabelFalse;
// this function is executed on load
$(function()
{
	fieldNotificationTrue=document.getElementById("id_NotificationTrue");
	fieldNotificationTrue.addEventListener("change", checkSettings);
	fieldNotificationFalse=document.getElementById("id_NotificationFalse");
	fieldNotificationFalse.addEventListener("change", checkSettings);
	if(window.location.href.indexOf("admin") > -1) 
	{
		var rows = document.getElementsByClassName("row");
		var i;
		for (i = 0; i < rows.length; i++) {
			//console.log(x[i].getElementsByClassName("control-group  field-IO"))
		    
		    if (rows[i].getElementsByClassName("control-group  field-LabelTrue").length>0)
	    	{
		    	rowfieldLabelTrue=rows[i];
		    	rowfieldLabelTrue.style.display = 'none';
	    	}
		    if (rows[i].getElementsByClassName("control-group  field-LabelFalse").length>0)
	    	{
		    	rowfieldLabelFalse=rows[i];
		    	rowfieldLabelFalse.style.display = 'none';
	    	}
		    
		}
	}else
	{
		var form = document.getElementsByClassName("form-horizontal");
		rowfieldLabelTrue=document.getElementById("div_id_LabelTrue");
		rowfieldLabelTrue.style.display = 'none';
		rowfieldLabelFalse=document.getElementById("div_id_LabelFalse");
		rowfieldLabelFalse.style.display = 'none';
		
	}
	
});

function checkSettings()
{
	if (fieldNotificationTrue.checked)
	{
		rowfieldLabelTrue.style.display='block';
	}else
	{
		rowfieldLabelTrue.style.display='none';
	}
	if (fieldNotificationFalse.checked)
	{
		rowfieldLabelFalse.style.display='block';
	}else
	{
		rowfieldLabelFalse.style.display='none';
	}
}
window.onload = checkSettings;