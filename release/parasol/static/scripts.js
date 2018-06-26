// SEE: https://sandbox.idre.ucla.edu/sandbox/general/zoomable-image-with-gdal-and-leaflet
// SEE: http://bl.ocks.org/bentrm/5aaedf8f2bd9361e280d

// script globals
var map;
var shadeBbox = [[42.3343660, -71.0825971], [42.3620201, -71.0453125]];
var shadeLayer;
var shadeUrls = [];
var start;
var end;
var startMarker;
var endMarker;
var route;
var animation;
var shadeLayers = [];
var hostIp;

// get route and update map
function updateRoute() {
    if (!start || !end) return; // abort if don't have two endpoints
    $.ajax({
        url: '/route',
        method: 'GET',
        data: {lat0: start.lat, lon0: start.lng, lat1: end.lat, lon1: end.lng},
        dataType: 'json',
        error: function(result) {
            console.log('Failed to fetch route, result:', result);
        },
        success: function(result) {
            console.log('Successfully fetched route, result:', result);
            if (route) route.remove();
            route = L.geoJSON(result);
            route.addTo(map);
        }
    });
};


//TODO: figure out how to make the geoserver IP more flexible
function updateShade() {
    var shadeIdx = parseInt($('#timeSlider')[0].value);
    // var newShadeLayer = L.tileLayer.wms('http://52.25.188.159:8080/geoserver/ows?', {
    var newShadeLayer = L.tileLayer.wms('http://localhost:8080/geoserver/ows?', {
        layers: shadeLayers[shadeIdx],
        opacity: 0.70
    }).addTo(map);
    if (shadeLayer) shadeLayer.remove();
    shadeLayer = newShadeLayer;
    console.log('Updated shade map to idx: ' + shadeIdx.toString() + ', layer: ', shadeLayers[shadeIdx]); 
};


// init - run on page load
$(document).ready(function() {
    
    // generate list of all shade layer names
    for (let tt = 500; tt <= 2200; tt += 100) {
        // generate image file path
        var tstr = tt.toString().padStart(4, "0");
        shadeLayers.push('parasol:sol_' + tstr.substring(0,2) + '.' +tstr.substring(2));
    } 
   
    // init the map object
    map = L.map('parasol-map', {
        center: [42.3481931, -71.0639548],
        zoom: 15
    });

    // add basemap
    var osmAttrib = 'Map data © <a href="http://openstreetmap.org">OpenStreetMap</a> contributors';
    var osm = L.tileLayer('http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 18,
        attribution: osmAttrib
    }).addTo(map); // this will be our active base layer on startup
    
    // init a map scale
    L.control.scale().addTo(map);

    // update slider properties
    var slider = $('#timeSlider')[0];
    slider.min = "0";
    slider.max = (shadeLayers.length - 5).toString(); // cut off night hours
    slider.value = "0";

    // add event listener for slider
    slider.oninput = updateShade;

    // update start location (left click)
    // TODO: make it an umbrella
    map.on('click', function(e) {
        start = e.latlng;
        if (startMarker) startMarker.remove();
        startMarker = L.marker(start);
        startMarker.addTo(map);
        updateRoute();
    });

    // update end location (right click)
    // TODO: make it an umbrella
    // TODO: apply different color
    map.on('contextmenu', function(e) {
        end = e.latlng;
        if (endMarker) endMarker.remove();
        endMarker = L.marker(end);
        endMarker.addTo(map);
        updateRoute();
    });

});
