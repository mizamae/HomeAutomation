//<script src="http://maps.google.com/maps/api/js?key=AIzaSyARa_5fk7pCUNLM9Ce_czcokqdVbn5PLyQ&sensor=false"></script>
//$.getScript("http://maps.google.com/maps/api/js?key=AIzaSyARa_5fk7pCUNLM9Ce_czcokqdVbn5PLyQ&sensor=false")

jQuery.loadScript = function (url, callback) {
    jQuery.ajax({
        url: url,
        dataType: 'script',
        success: callback,
        async: true
    });
}
if (typeof google == 'undefined') $.loadScript('http://maps.google.com/maps/api/js?key=AIzaSyARa_5fk7pCUNLM9Ce_czcokqdVbn5PLyQ&sensor=false', function(){
    //Stuff to do after someScript has loaded
	var h2=document.createElement("DIV");
    h2.innerHTML="Click on the map to obtain coordinates";
    var mapdiv=document.createElement("DIV");
	mapdiv.className="col-md-8";
	mapdiv.setAttribute("id", "map-container");
	var contentMain=document.getElementById("content-main");
    contentMain.appendChild(h2);
	contentMain.appendChild(mapdiv);
	google.maps.event.addDomListener(window, 'load', init_map);
});


function init_map() {
     // Enter the latitude and longitude of your office here
	 var latitude=document.getElementById("id_Latitude").value;
     var longitude=document.getElementById("id_Longitude").value;
     var name=document.getElementById("id_Identifier").value;
     
     if (latitude!="" & longitude!="")
     {
         var myLocation = new google.maps.LatLng(latitude,longitude);
         var marker = new google.maps.Marker({
										position: myLocation,
										title:name});
        
                                        
     }else
     {
         var myLocation = new google.maps.LatLng(42.793759,-1.615882);
         
     }
        
     var mapOptions = {
				center: myLocation,
				zoom: 14
				};

	 

     var map = new google.maps.Map(document.getElementById("map-container"),
										mapOptions);
    if (marker) {marker.setMap(map);}
	 google.maps.event.addListener(map, "click", function (e) {
		    //lat and lng is available in e object
		    var latLng = e.latLng;
		    var LatitudeField=document.getElementById("id_Latitude");
		    var LongitudeField=document.getElementById("id_Longitude");
		    LatitudeField.value=latLng.lat();
		    LongitudeField.value=latLng.lng();
		    console.log('Position: ' + latLng.toString())
		});
}


   