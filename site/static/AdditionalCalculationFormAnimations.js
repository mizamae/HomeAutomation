var fieldUnits,fieldSourceVar2,fieldTwoVarsOperation,fieldCalculation;
var rowfieldUnits,rowfieldSourceVar2,rowfieldTwoVarsOperation;

var group;
var fieldset;
var table;

// this function is executed on load
$(function()
{
	var rows = document.getElementsByClassName("row");
	var i;
	for (i = 0; i < rows.length; i++) {
		if (rows[i].getElementsByClassName("control-group  field-SourceVar2").length>0)
    	{
	    	fieldSourceVar2=document.getElementById("id_SourceVar2");
	    	rowfieldSourceVar2=rows[i];
    		rows[i].style.display = 'none';
    	}
		if (rows[i].getElementsByClassName("control-group  field-TwoVarsOperation").length>0)
    	{
			fieldTwoVarsOperation=document.getElementById("id_TwoVarsOperation");
	    	rowfieldTwoVarsOperation=rows[i];
    		rows[i].style.display = 'none';
    	}
		if (rows[i].getElementsByClassName("control-group  field-Units").length>0)
    	{
			fieldUnits=document.getElementById("id_Units");
			rowfieldUnits=rows[i];
    		rows[i].style.display = 'none';
    	}
		if (rows[i].getElementsByClassName("control-group  field-Calculation").length>0)
    	{
	    	fieldCalculation=document.getElementById("id_Calculation");
	    	rowfieldCalculation=rows[i];
	    	rows[i].addEventListener("change", CalculationTypeChange);
    	}
	}
	
	
	CalculationTypeChange();
});


function CalculationTypeChange()
{ 
	//selectedAction="7" - > operation with two variables

	
	var selectedAction=fieldCalculation.options[fieldCalculation.selectedIndex].value;
	if (selectedAction=="7"){
		rowfieldSourceVar2.style.display = 'block';
		rowfieldTwoVarsOperation.style.display = 'block';
		rowfieldUnits.style.display = 'block';
	}
	else{
		rowfieldSourceVar2.style.display = 'none';
		rowfieldTwoVarsOperation.style.display = 'none';
		rowfieldUnits.style.display = 'none';
	}
	
}
