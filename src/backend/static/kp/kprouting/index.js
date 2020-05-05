var map = L.map('map');
map.invalidateSize();

L.tileLayer('https://{s}.tile.osm.org/{z}/{x}/{y}.png', { // http://localhost:5008/tile/{z}/{x}/{y}.png', { // 
    attribution: 'openstreetmap.org'
}).addTo(map);

var global_center_latlong = null
var routingControl = null

/*       https://a.tile.openstreetmap.org/
// For MY

// Starting, For UK
var from_latlng = [51.447250, -0.189370]
var to_latlng = [51.50744689, 0.065910331]
*/


/*
var routingControl = L.Routing.control(L.extend(window.lrmConfig, {
    waypoints: [
        L.latLng(from_latlng[0], from_latlng[1]),
        L.latLng(to_latlng[0], to_latlng[1])
    ],
    geocoder: L.Control.Geocoder.nominatim(),
    routeWhileDragging: false,
    reverseWaypoints: true,
    showAlternatives: true,
    altLineOptions: {
        styles: [
            { color: 'black', opacity: 0.15, weight: 9 },
            { color: 'white', opacity: 0.8, weight: 6 },
            { color: 'blue', opacity: 0.5, weight: 2 }
        ]
    }
})).addTo(map);

L.Routing.errorControl(routingControl).addTo(map);


 */


// var routingControl = null;

// https://github.com/Leaflet/Leaflet.Icon.Glyph

var addRoutingControl = function(waypoints) {
    if (routingControl != null)
        removeRoutingControl();


    routingControl = L.Routing.control({
        waypoints: waypoints,
        createMarker: function(i, start, n) {
            var marker_icon = null
            if (i == 0) {
                // This is the first marker, indicating start
                marker_icon = L.icon.glyph({
                    prefix: '',
                    glyph: 'S'
                })
            } else if (i == n - 1) {
                //This is the last marker indicating destination
                marker_icon = L.icon.glyph({
                    prefix: '',
                    glyph: 'E'
                })
            }
            var marker = L.marker(start.latLng, {
                draggable: true,
                bounceOnAdd: false,
                bounceOnAddOptions: {
                    duration: 1000,
                    height: 800,
                    function() {
                        (bindPopup(myPopup).openOn(map))
                    }
                },
                icon: marker_icon
            })
            return marker
        }
    }).addTo(map);
    L.Routing.errorControl(routingControl).addTo(map);
};





var removeRoutingControl = function() {
    if (routingControl != null) {
        map.removeControl(routingControl);
        routingControl = null;
    }
};

var show_job_route = function(from_latlng, to_latlng) {

    global_center_latlong = [
        (from_latlng[0] + to_latlng[0]) / 2,
        ((from_latlng[1] + to_latlng[1]) / 2) + 0.2
    ]
    removeRoutingControl()
    addRoutingControl([
        L.latLng(from_latlng[0], from_latlng[1]),
        L.latLng(to_latlng[0], to_latlng[1])
        //		L.latLng( 3.5245169,	101.90809300000001 ),
        //L.latLng(3.2662035,	101.64786009999999)
    ])
    $('#myModal').modal('show')

};


// https://stackoverflow.com/questions/49305901/leaflet-and-mapbox-in-modal-not-displaying-properly
// Comment out the below code to see the difference.
$('#myModal').on('shown.bs.modal', function() {

    setTimeout(function() {
        map.invalidateSize();
        /*
        var center_latlong = [
            (from_latlng[0] + to_latlng[0]) / 2,
            ((from_latlng[1] + to_latlng[1]) / 2) + 0.2
        ]
        */

        map.setView(global_center_latlong, 10)

    }, 10);
    //map.invalidateSize();
});





/*
$('#myModal').modal(options)

map.whenReady(() => {
    console.log('Map ready');
    setTimeout(() => {
		map.invalidateSize();
		//map.setZoom(10)   [3.5245169,	101.90809300000001]
		var center_latlong = [
			(from_latlng[0]+ to_latlng[0] ) / 2 ,
			(from_latlng[1]+ to_latlng[1] ) / 2  
			]


		map.setView(center_latlong,9)
    }, 0);
});
*/