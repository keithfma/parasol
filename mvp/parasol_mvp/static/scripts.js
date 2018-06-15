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


function updateShade() {
    var shadeIdx = parseInt($('#timeSlider')[0].value);
    if (shadeLayer) shadeLayer.remove();
    shadeLayer = L.imageOverlay(shadeUrls[shadeIdx], shadeBbox, {opacity: .9})
    shadeLayer.addTo(map);
    console.log('Updated shade map to idx: ' + shadeIdx.toString() + ", url: " + shadeUrls[shadeIdx]); 
};


// init - run on page load
$(document).ready(function() {
    
    // generate list of all shade image urls
    for (let tt = 0; tt <= 2400; tt += 25) {
        // generate image file path
        var tstr = tt.toString().padStart(4, "0");
        shadeUrls.push('/img/shade_' + tstr.substring(0,2) + '.' +tstr.substring(2) + '.png');
    } 

    // select initial shade image
    // TODO: set initial layer by current time
    var initShadeIdx = 40; // 10 AM
    
    // update slider properties
    var slider = $('#timeSlider')[0];
    slider.min = "15";
    slider.max = "80"; // shadeUrls.length.toString();
    slider.value = initShadeIdx;

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

    // // add initial shade map
    shadeLayer = L.imageOverlay(shadeUrls[initShadeIdx], shadeBbox, {opacity: .9})

    // init a map scale
    L.control.scale().addTo(map);

    // init a simple layer switcher with overlays an mutual exclusive base layers
    var baseLayers = {"Map": osm}
    var overlays = {"Shade": shadeLayer};
    L.control.layers(baseLayers, overlays, {collapsed: false}).addTo(map);

    // add event listener for slider
    slider.onchange = updateShade;

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
