var fieldIO,fieldIOValue,fieldActionType,fieldDevice,fieldOrder,fieldIsConstant,fieldConstant;
var rowfieldIO,rowfieldIOValue,rowfieldDevice,rowfieldOrder,rowfieldConstant,rowfieldVar2;

var group;
var fieldset;
var table;

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
	
	group=document.getElementById("ruleitem_set-group");
	fieldset=$(group).children("div")[0];
	fieldset=$(fieldset).children("fieldset.module")[0];
	table=$(fieldset).children("table")[0];
	
	IsConstantInit()
	ActionTypeChange();
	DeviceChange();
	AddNewRuleItem();
});

function bindAddNew()
{
	for(var i = 0; i < table.rows.length; i++)
	{
		var row=table.rows[i];
		if (row.className.includes("add-row"))
		{
			var AddCell=$(row).children("td")[0];
			var Link=$(AddCell).children("a")[0];
			Link.addEventListener("click", AddNewRuleItem);
		}
	}
}
window.onload = bindAddNew;

function AddNewRuleItem()
{
	for(var i = 0; i < table.rows.length; i++)
	{
		var row=table.rows[i];
		if (row.className.includes("empty-form"))
		{
			row=table.rows[i-1];
			if (row.className.includes("dynamic-ruleitem_set") || row.className.includes("has_original"))
			{
				var Operator3Cell=row.getElementsByClassName("field-Operator3")[0];
				var Operator3Select=$(Operator3Cell).children("select")[0];
				Operator3Select.disabled=true;
				var DeleteCell=row.getElementsByClassName("delete")[0];
				var DeleteLink=$(DeleteCell).children("div")[0];
				DeleteLink=$(DeleteLink).children("a")[0];
				if (DeleteLink){DeleteLink.addEventListener("click", function(){DeleteRuleItem(i-1);});}
			}
			row=table.rows[i-2];
			if (row.className.includes("dynamic-ruleitem_set")|| row.className.includes("has_original"))
			{
				var Operator3Cell=row.getElementsByClassName("field-Operator3")[0];
				var Operator3Select=$(Operator3Cell).children("select")[0];
				Operator3Select.disabled=false;
			}
			break;
		}
	}
}

function DeleteRuleItem(rownum)
{
	if (rownum > table.rows.length-3)
	{
		var row=table.rows[rownum-1];
		if (row.className.includes("dynamic-ruleitem_set") || row.className.includes("has_original"))
		{
			var Operator3Cell=row.getElementsByClassName("field-Operator3")[0];
			var Operator3Select=$(Operator3Cell).children("select")[0];
			Operator3Select.value='';
			Operator3Select.disabled=true;
		}
	}
}

function IsConstantInit()
{
	var checkboxes=$("input:checkbox");
	for(var i = 0; i < checkboxes.length; i++) 
	{
		if (checkboxes[i].name.includes("ruleitem_set"))
		{
			checkboxes[i].addEventListener("change", checkIsConstants);
			checkIsConstants();
		}
			
	}
}

function checkIsConstants()
{
	for(var i = 0; i < table.rows.length; i++)
	{
		var row=table.rows[i];
		if (row.className.includes("form-row"))
		{
			if (row.className.includes("empty-form"))
			{	break;}
			else
			{
				var IsConstantCell=row.getElementsByClassName("field-IsConstant")[0];
				var IsConstant=$(IsConstantCell).children("input")[0];
				var Var2Cell=row.getElementsByClassName("field-Var2")[0];
				var Var2Input=$(Var2Cell).children("div")[0];
				Var2Input=$(Var2Input).children("select")[0];
				var ConstantCell=row.getElementsByClassName("field-Constant")[0];
				var ConstantInput=$(ConstantCell).children("input")[0];
				
				if (IsConstant.checked)
				{
					Var2Input.value='';
					Var2Input.disabled=true;
					ConstantInput.disabled=false;
				}else
				{
					Var2Input.disabled=false;
					ConstantInput.disabled=true;
				}
			}
		}
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