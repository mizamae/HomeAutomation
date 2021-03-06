var rows = document.getElementsByClassName("row");
var i;
var fieldIO,fieldDeviceCode,fieldType,fieldDeviceIP,fieldSampletime,fieldRTSampletime,fieldPort,fieldBaudrate,fieldParity,fieldStopbit;
var rowfieldIO,rowfieldDeviceCode,rowfieldType,rowfieldDeviceIP,rowfieldSampletime,rowfieldRTSampletime,rowfieldPort,rowfieldBaudrate,rowfieldParity,rowfieldStopbit;
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
		    if (rows[i].getElementsByClassName("control-group  field-Sampletime").length>0)
	    	{
		    	fieldSampletime=document.getElementById("id_Sampletime");
		    	rowfieldSampletime=rows[i];
		    	rowfieldSampletime.style.display = 'block';
	    	}
		    if (rows[i].getElementsByClassName("control-group  field-RTsampletime").length>0)
	    	{
		    	fieldRTsampletime=document.getElementById("id_RTsampletime");
		    	rowfieldRTSampletime=rows[i];
		    	rowfieldRTSampletime.style.display = 'block';
	    	}
		    if (rows[i].getElementsByClassName("control-group  field-Port").length>0)
	    	{
		    	fieldPort=document.getElementById("id_Port");
		    	rowfieldPort=rows[i];
		    	rowfieldPort.style.display = 'none';
	    	}
		    if (rows[i].getElementsByClassName("control-group  field-Baudrate").length>0)
	    	{
		    	fieldBaudrate=document.getElementById("id_Baudrate");
		    	rowfieldBaudrate=rows[i];
		    	rowfieldBaudrate.style.display = 'none';
	    	}
		    if (rows[i].getElementsByClassName("control-group  field-Parity").length>0)
	    	{
		    	fieldParity=document.getElementById("id_Parity");
		    	rowfieldParity=rows[i];
		    	rowfieldParity.style.display = 'none';
	    	}
		    if (rows[i].getElementsByClassName("control-group  field-Stopbits").length>0)
	    	{
		    	fieldStopbits=document.getElementById("id_Stopbits");
		    	rowfieldStopbits=rows[i];
		    	rowfieldStopbits.style.display = 'none';
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
		
		fieldPort=document.getElementById("id_Port");
		rowfieldPort=document.getElementById("div_id_Port");
		rowfieldPort.style.display = 'none';
		fieldBaudrate=document.getElementById("id_Baudrate");
		rowfieldBaudrate=document.getElementById("div_id_Baudrate");
		rowfieldBaudrate.style.display = 'none';
		fieldParity=document.getElementById("id_Parity");
		rowfieldParity=document.getElementById("div_id_Parity");
		rowfieldParity.style.display = 'none';
		fieldStopbits=document.getElementById("id_Stopbits");
		rowfieldStopbits=document.getElementById("div_id_Stopbits");
		rowfieldStopbits.style.display = 'none';
	}
	TypeChange();
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
		    	if (response.Connection == 0) // local connection
		    	{
		    		rowfieldIO.style.display = 'block';
		    		rowfieldDeviceIP.style.display = 'none';
		    		fieldDeviceIP.value=null;
		    		rowfieldDeviceCode.style.display = 'none';
		    		fieldDeviceCode.value=null;
		    		
		    		rowfieldPort.style.display = 'none';
		    		rowfieldParity.style.display = 'none';
		    		rowfieldBaudrate.style.display = 'none';
		    		fieldBaudrate.value=9600;
		    		rowfieldStopbits.style.display = 'none';
		    		fieldStopbits.value=1;
		    		
		    	}
		    	else if (response.Connection == 1) // REMOTE_TCP_CONNECTION
	    		{
		    		rowfieldIO.style.display = 'none';
		    		fieldIO.value=null;
		    		rowfieldDeviceIP.style.display = 'block';
		    		rowfieldDeviceCode.style.display = 'none';
		    		
		    		rowfieldPort.style.display = 'none';
		    		rowfieldParity.style.display = 'none';
		    		rowfieldBaudrate.style.display = 'none';
		    		fieldBaudrate.value=9600;
		    		rowfieldStopbits.style.display = 'none';
		    		fieldStopbits.value=1;
	    		}
		    	else if (response.Connection == 2) // MEMORY_CONNECTION
	    		{
		    		rowfieldIO.style.display = 'none';
		    		fieldIO.value=null;
		    		rowfieldDeviceIP.style.display = 'none';
		    		fieldDeviceIP.value=null;
		    		rowfieldDeviceCode.style.display = 'none';
		    		fieldDeviceCode.value=null;
		    		
		    		rowfieldPort.style.display = 'none';
		    		rowfieldParity.style.display = 'none';
		    		rowfieldBaudrate.style.display = 'none';
		    		fieldBaudrate.value=9600;
		    		rowfieldStopbits.style.display = 'none';
		    		fieldStopbits.value=1;
	    		}
		    	else if (response.Connection == 3) // REMOTE_RS485_CONNECTION
	    		{
		    		rowfieldIO.style.display = 'none';
		    		fieldIO.value=null;
		    		rowfieldDeviceIP.style.display = 'none';
		    		fieldDeviceIP.value=null;
		    		rowfieldDeviceCode.style.display = 'block';
		    		fieldDeviceCode.value=0;
		    		
		    		rowfieldPort.style.display = 'block';
		    		rowfieldParity.style.display = 'block';
		    		rowfieldBaudrate.style.display = 'block';
		    		rowfieldStopbits.style.display = 'block';
	    		}
		    	else{}
		        console.log(response)
		    },
		    error: function(jqXHR, textStatus, errorThrown) {
		    	 console.log(errorThrown);
		    }
		});
	}
}

