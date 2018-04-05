var rows = document.getElementsByClassName("row");
var i;
var fieldIO,fieldDeviceCode,fieldType,fieldDeviceIP;
var rowfieldIO,rowfieldDeviceCode,rowfieldType,rowfieldDeviceIP;
// this function is executed on load
$(function()
{
	if(window.location.href.indexOf("admin") > -1) 
	{
		var rows = document.getElementsByClassName("row");
		var i;
		for (i = 0; i < rows.length; i++) {
			//console.log(x[i].getElementsByClassName("control-group  field-IO"))
		    if (rows[i].getElementsByClassName("control-group  field-IO").length>0)
	    	{
		    	fieldIO=document.getElementById("id_IO");
		    	rowfieldIO=rows[i];
		    	rowfieldIO.style.display = 'none';
	    	}
		    if (rows[i].getElementsByClassName("control-group  field-Code").length>0)
	    	{
		    	fieldDeviceCode=document.getElementById("id_Code");
		    	rowfieldDeviceCode=rows[i];
		    	rowfieldDeviceCode.style.display = 'none';
	    	}
		    if (rows[i].getElementsByClassName("control-group  field-DVT").length>0)
	    	{
		    	fieldType=document.getElementById("id_DVT");
		    	rowfieldType=rows[i];
		    	rowfieldType.addEventListener("change", TypeChange);
	    	}
		    if (rows[i].getElementsByClassName("control-group  field-IP").length>0)
	    	{
		    	fieldDeviceIP=document.getElementById("id_IP");
		    	rowfieldDeviceIP=rows[i];
		    	rowfieldDeviceIP.style.display = 'none';
	    	}
		    
		}
	}else
	{
		var form = document.getElementsByClassName("form-horizontal");
		fieldIO=document.getElementById("id_IO");
		rowfieldIO=document.getElementById("div_id_IO");
		rowfieldIO.style.display = 'none';
		fieldDeviceCode=document.getElementById("id_Code");
		fieldDeviceCode.readOnly = true;
		rowfieldDeviceCode=document.getElementById("div_id_Code");
		rowfieldDeviceCode.style.display = 'none';
		fieldType=document.getElementById("id_DVT");
		fieldType.addEventListener("change", TypeChange);
		fieldType.readOnly = true;
		rowfieldType=document.getElementById("div_id_DVT");
		fieldDeviceIP=document.getElementById("id_IP");
		fieldDeviceIP.readOnly = true;
		rowfieldDeviceIP=document.getElementById("div_id_IP");
		rowfieldDeviceIP.style.display = 'none';
		TypeChange();
	}
});

function TypeChange()
{ 	
	var selectedType=fieldType.options[fieldType.selectedIndex].value;
	if (selectedType!="")
	{
		var data=JSON.stringify({DeviceTypePK: selectedType});
		$.ajax({
		    url: '/Devices/ajax_get_data_for_devicetype/' + selectedType,
		    type: 'GET',
		    data:  data,
		    dataType: "html",
		    success: function(result){
		    	var response=JSON.parse(result);
		    	if (response.Connection == 0)
		    	{
		    		rowfieldIO.style.display = 'block';
		    		rowfieldDeviceIP.style.display = 'none';
		    		fieldDeviceIP.value=null;
		    		rowfieldDeviceCode.style.display = 'none';
		    		fieldDeviceCode.value=null;
		    	}
		    	else if (response.Connection == 1)
	    		{
		    		rowfieldIO.style.display = 'none';
		    		fieldIO.value=null;
		    		rowfieldDeviceIP.style.display = 'block';
		    		rowfieldDeviceCode.style.display = 'block';
	    		}
		    	else if (response.Connection == 2)
	    		{
		    		rowfieldIO.style.display = 'none';
		    		fieldIO.value=null;
		    		rowfieldDeviceIP.style.display = 'none';
		    		fieldDeviceIP.value=null;
		    		rowfieldDeviceCode.style.display = 'none';
		    		fieldDeviceCode.value=null;
	    		}
		    	else{}
		        console.log(response)
		    },
		    error: function(jqXHR, textStatus, errorThrown) {
		    	rowfieldOrder.style.display = 'none';
		    	console.log(errorThrown);
		    }
		});
	}
}

