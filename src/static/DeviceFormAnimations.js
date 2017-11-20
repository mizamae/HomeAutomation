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
		    if (rows[i].getElementsByClassName("control-group  field-DeviceCode").length>0)
	    	{
		    	fieldDeviceCode=document.getElementById("id_DeviceCode");
		    	rowfieldDeviceCode=rows[i];
		    	rowfieldDeviceCode.style.display = 'none';
	    	}
		    if (rows[i].getElementsByClassName("control-group  field-Type").length>0)
	    	{
		    	fieldType=document.getElementById("id_Type");
		    	rowfieldType=rows[i];
		    	rowfieldType.addEventListener("change", TypeChange);
	    	}
		    if (rows[i].getElementsByClassName("control-group  field-DeviceIP").length>0)
	    	{
		    	fieldDeviceIP=document.getElementById("id_DeviceIP");
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
		fieldDeviceCode=document.getElementById("id_DeviceCode");
		fieldDeviceCode.readOnly = true;
		rowfieldDeviceCode=document.getElementById("div_id_DeviceCode");
		rowfieldDeviceCode.style.display = 'none';
		fieldType=document.getElementById("id_Type");
		fieldType.readOnly = true;
		rowfieldType=document.getElementById("div_id_Type");
		fieldDeviceIP=document.getElementById("id_DeviceIP");
		fieldDeviceIP.readOnly = true;
		rowfieldDeviceIP=document.getElementById("div_id_DeviceIP");
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
		    url: '/ajax_get_data_for_devicetype/' + selectedType,
		    type: 'GET',
		    data:  data,
		    dataType: "html",
		    success: function(result){
		    	var response=JSON.parse(result);
		    	if (response.Connection == 'LOCAL')
		    	{
		    		rowfieldIO.style.display = 'block';
		    		rowfieldDeviceIP.style.display = 'none';
		    		fieldDeviceIP.value=null;
		    		rowfieldDeviceCode.style.display = 'none';
		    		fieldDeviceCode.value=null;
		    	}
		    	else if (response.Connection == 'REMOTE')
	    		{
		    		rowfieldIO.style.display = 'none';
		    		fieldIO.value=null;
		    		rowfieldDeviceIP.style.display = 'block';
		    		rowfieldDeviceCode.style.display = 'block';
	    		}
		    	else if (response.Connection == 'MEMORY')
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

