var rows = document.getElementsByClassName("row");
var i;
var fieldIO,fieldIOValue,fieldActionType,fieldDevice,fieldOrder,fieldIsConstant,fieldConstant;
var rowfieldIO,rowfieldIOValue,rowfieldDevice,rowfieldOrder,rowfieldConstant,rowfieldVar2;
// this function is executed on load
$(function()
{
	var rows = document.getElementsByClassName("row");
	var i;
	for (i = 0; i < rows.length; i++) {
		//console.log(x[i].getElementsByClassName("control-group  field-IO"))
	    if (rows[i].getElementsByClassName("control-group  field-IO").length>0)
    	{
	    	fieldIO=document.getElementById("id_IO");
	    	rowfieldIO=rows[i];
    		//rows[i].style.display = 'none';
    	}
	    if (rows[i].getElementsByClassName("control-group  field-IOValue").length>0)
    	{
	    	fieldIOValue=document.getElementById("id_IOValue");
	    	rowfieldIOValue=rows[i];
    		//rows[i].style.display = 'none';
    	}
	    if (rows[i].getElementsByClassName("control-group  field-Device").length>0)
    	{
	    	fieldDevice=document.getElementById("id_Device");
	    	rowfieldDevice=rows[i];
	    	rows[i].style.display = 'none';
	    	rows[i].addEventListener("change", DeviceChange);
    	}
	    if (rows[i].getElementsByClassName("control-group  field-Order").length>0)
    	{
	    	fieldOrder=document.getElementById("id_Order");
	    	rowfieldOrder=rows[i];
	    	rows[i].style.display = 'none';
    	}
	    
	    if (rows[i].getElementsByClassName("control-group  field-ActionType").length>0)
    	{
	    	fieldActionType=document.getElementById("id_ActionType");
	    	rows[i].addEventListener("change", ActionTypeChange);
    	}
	    if (rows[i].getElementsByClassName("control-group  field-IsConstant").length>0)
    	{
	    	fieldIsConstant=document.getElementById("id_IsConstant");
	    	rows[i].addEventListener("change", IsConstantChange);
    	}
	    if (rows[i].getElementsByClassName("control-group  field-Constant").length>0)
    	{
	    	fieldConstant=document.getElementById("id_Constant");
	    	rowfieldConstant=rows[i];
	    	rowfieldConstant.style.display = 'none';
    	}
	    if (rows[i].getElementsByClassName("control-group  field-Var2").length>0)
    	{
	    	rowfieldVar2=rows[i];
    	}
	}
	IsConstantChange();
	ActionTypeChange();
	DeviceChange();
});

function IsConstantChange()
{
	if (fieldIsConstant.checked)
	{
		rowfieldConstant.style.display = 'block';
		rowfieldVar2.style.display = 'none';
	}else
	{
		rowfieldConstant.style.display = 'none';
		rowfieldVar2.style.display = 'block';
	}
}

function ActionTypeChange()
{ 
	//selectedAction="a" - > Activate output on Main
	//selectedAction="b" - > Send command to a device
	//selectedAction="c" - > Send email
	
	var selectedAction=fieldActionType.options[fieldActionType.selectedIndex].value;
	if (selectedAction=="a"){rowfieldIO.style.display = 'block';rowfieldIOValue.style.display = 'block';}
	else{rowfieldIO.style.display = 'none';rowfieldIOValue.style.display = 'none';}
	if (selectedAction=="b")
	{rowfieldDevice.style.display = 'block';}
	else{rowfieldDevice.style.display = 'none';
		rowfieldOrder.style.display = 'none';}
}

function DeviceChange()
{
	var selectedDevice=fieldDevice.options[fieldDevice.selectedIndex].value;
	if (selectedDevice!="")
	{
		var data=JSON.stringify({DevicePK: selectedDevice});
		$.ajax({
		    url: '/ajax_get_orders_for_device/' + selectedDevice,
		    type: 'GET',
		    data:  data,
		    dataType: "html",
		    success: function(result){
		    	rowfieldOrder.style.display = 'block';
		    	var response=JSON.parse(result);
		    	var length = fieldOrder.options.length;
		    	for (i = 0; i < length; i++) {
		    		fieldOrder.options[i] = null;
		    	}
		    	for (i=0;i<response.length;i++)
		    	{
		    		fieldOrder.append(response[i].HumanTag);
		    	}
		        console.log(response)
		    },
		    error: function(jqXHR, textStatus, errorThrown) {
		    	rowfieldOrder.style.display = 'none';
		    	console.log(errorThrown);
		    }
		});
	}
}