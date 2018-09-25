var rows = document.getElementsByClassName("row");
var i;
var fieldType,fieldCron;
var rowfieldType,rowfieldCron;
// this function is executed on load
$(function()
{
	if(window.location.href.indexOf("admin") > -1) 
	{
		var rows = document.getElementsByClassName("row");
		var i;
		for (i = 0; i < rows.length; i++) {
			//console.log(x[i].getElementsByClassName("control-group  field-IO"))
		    if (rows[i].getElementsByClassName("control-group  field-Type").length>0)
	    	{
		    	fieldType=document.getElementById("id_Type");
		    	rowfieldType=rows[i];
		    	rowfieldType.style.display = 'block';
		    	rowfieldType.addEventListener("change", TypeChange);
	    	}
		    if (rows[i].getElementsByClassName("control-group  field-Cron").length>0)
	    	{
		    	fieldCron=document.getElementById("id_Cron");
		    	rowfieldCron=rows[i];
		    	rowfieldCron.style.display = 'none';
	    	}
		    
		}
	}else
	{
		var form = document.getElementsByClassName("form-horizontal");
		fieldType=document.getElementById("id_Type");
		rowfieldType=document.getElementById("div_id_Type");
		rowfieldType.style.display = 'block';
		fieldCron=document.getElementById("id_Cron");
		rowfieldCron=document.getElementById("div_id_Cron");
		rowfieldCron.style.display = 'none';
	}
	TypeChange();
});

function TypeChange()
{ 	
	var selectedType=fieldType.options[fieldType.selectedIndex].value;
	if (selectedType!="")
	{
		if (selectedType == "2")
    	{
			rowfieldCron.style.display = 'block';
    	}
    	else 
		{
    		rowfieldCron.style.display = 'none';
		}
	}
}

