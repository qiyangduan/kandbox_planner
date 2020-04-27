/*
window.lrmConfig = {
    //    serviceUrl: 'https://api.mapbox.com/directions/v5',
    //    profile: 'mapbox/driving',
    //label: 'Car (fastest)',
    //path: 'https://router.project-osrm.org/route/v1'
    //serviceUrl: 'http://localhost:5000/route/v1',
    //serviceUrl: '/route/v1',
    serviceUrl: 'https://planner.kandbox.com/route/v1',
    profile: 'driving',
};


// https://stackoverflow.com/questions/46542342/completely-remove-leaflet-route

MapHelper = (function ($) {
    'use strict';

    var settings = {
        center: [0, 0],
        zoom: null,
    };

    var mapId = '';
    var map = null;
    var baseMaps = {};
    var overlayMaps = {};
    var routingControl = null;


    var init = function (mapLayerId, options) {
        settings = $.extend(settings, options);
        mapId = mapLayerId;
        initMap();
    };

    var getMap = function () {
        return map;
    };

    var addRoutingControl = function (waypoints) { 
        if (routingControl != null)
            removeRoutingControl();

        routingControl = L.Routing.control({
            waypoints: waypoints
        }).addTo(map);
    };

    var removeRoutingControl = function () {
        if (routingControl != null) {
            map.removeControl(routingControl);
            routingControl = null;
        }
    };

    var panMap = function (lat, lng) {
        map.panTo(new L.LatLng(lat, lng));
    }

    var centerMap = function (e) {
        panMap(e.latlng.lat, e.latlng.lng);
    }

    var zoomIn = function (e) {
        map.zoomIn();
    }

    var zoomOut = function (e) {
        map.zoomOut();
    }

    var initMap = function () {
        var $this = this;

        map = L.map(mapId, {
            center: settings.center,
            zoom: settings.zoom,
            crs: L.CRS.EPSG3857,
            attributionControl: true,
            contextmenu: true,
            contextmenuWidth: 140
        });

        baseMaps["OSM"] = L.tileLayer('http://{s}.tile.osm.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="http://osm.org/copyright" target="_blank">OpenStreetMap</a> contributors'
        }).addTo(map);
    };

    var invalidateMapSize = function () {
        map.invalidateSize();
    }

    return {
        init: init, addRoutingControl: addRoutingControl, removeRoutingControl: removeRoutingControl, 
        panMap: panMap, invalidateMapSize: invalidateMapSize, getMap: getMap
    }
}(jQuery));




MapHelper.init('map', {
	osm: false,
	bing: true,
	zoom: 10,
	center: L.latLng(51.509865, -0.118092),
});

$('#addRoute').on('click', function() {
	MapHelper.addRoutingControl( [
		L.latLng(50.509865, -1.118092),
		L.latLng(51.509865, -0.118092)
	]);
});

$('#remoteRoute').on('click', function() {
	MapHelper.removeRoutingControl();
});
*/