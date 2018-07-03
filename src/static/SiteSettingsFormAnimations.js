var field_PROXY_AUTO_DENYIP,field_PROXY_CREDENTIALS;
var row_AUTODENY_ATTEMPTS,row_PROXY_USER1,row_PROXY_PASSW1,row_PROXY_USER2,row_PROXY_PASSW2;
var currentValues,originalFontColor;
// this function is executed on load
$(function()
{
	field_PROXY_AUTO_DENYIP=document.getElementById("id_PROXY_AUTO_DENYIP");
	field_PROXY_AUTO_DENYIP.addEventListener("click", checkSettings);
	row_AUTODENY_ATTEMPTS=document.getElementById("div_id_AUTODENY_ATTEMPTS");
	field_PROXY_CREDENTIALS=document.getElementById("id_PROXY_CREDENTIALS");
	field_PROXY_CREDENTIALS.addEventListener("click", checkSettings);
	row_PROXY_USER1=document.getElementById("div_id_PROXY_USER1");
	row_PROXY_PASSW1=document.getElementById("div_id_PROXY_PASSW1");
	row_PROXY_USER2=document.getElementById("div_id_PROXY_USER2");
	row_PROXY_PASSW2=document.getElementById("div_id_PROXY_PASSW2");
	originalFontColor=document.getElementById("id_FACILITY_NAME").style.color;
});

function checkSettings()
{
	if (field_PROXY_AUTO_DENYIP.checked)
	{
		row_AUTODENY_ATTEMPTS.style.display='block';
	}else
	{
		row_AUTODENY_ATTEMPTS.style.display='none';
	}
	if (field_PROXY_CREDENTIALS.checked)
	{
		row_PROXY_USER1.style.display='block';
		row_PROXY_PASSW1.style.display='block';
		row_PROXY_USER2.style.display='block';
		row_PROXY_PASSW2.style.display='block';
	}else
	{
		row_PROXY_USER1.style.display='none';
		row_PROXY_PASSW1.style.display='none';
		row_PROXY_USER2.style.display='none';
		row_PROXY_PASSW2.style.display='none';
	}
}
window.onload = checkSettings;

function checkIfChanged(field2check)
{

	if (field2check.value!=currentValues.fields[field2check.name])
	{
		field2check.style.color = "#ff0000";
		console.log('Ha cambiado!!')
	}else
	{
		field2check.style.color = originalFontColor;
	}

}