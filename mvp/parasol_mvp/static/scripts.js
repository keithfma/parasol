// SEE: https://sandbox.idre.ucla.edu/sandbox/general/zoomable-image-with-gdal-and-leaflet
// SEE: http://bl.ocks.org/bentrm/5aaedf8f2bd9361e280d

// script globals
var shadeBbox = [[42.3343660, -71.0825971], [42.3620201, -71.0453125]];
var shadeLayer;
var shadeUrls = [];
var lon0;
var lat0;
var lon1;
var lat1;


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
    slider.min = "0";
    slider.max = shadeUrls.length.toString();
    slider.value = initShadeIdx;

    // init the map object
    var map = L.map('parasol-map', {
        center: [42.3481931, -71.0639548],
        zoom: 15
    });

    // add basemap
    var osmAttrib = 'Map data © <a href="http://openstreetmap.org">OpenStreetMap</a> contributors';
    var osm = L.tileLayer('http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 18,
        attribution: osmAttrib
    }).addTo(map); // this will be our active base layer on startup

    // add initial shade map
    shadeLayer = L.imageOverlay(shadeUrls[initShadeIdx], shadeBbox, {opacity: .9})
    shadeLayer.addTo(map);

    // init a map scale
    L.control.scale().addTo(map);

    // init a simple layer switcher with overlays an mutual exclusive base layers
    var baseLayers = {"Map": osm}
    var overlays = {"Shade": shadeLayer};
    L.control.layers(baseLayers, overlays, {collapsed: false}).addTo(map);

    // add event listener for slider
    slider.onchange= function() {
        var shadeIdx = parseInt($('#timeSlider')[0].value);
        shadeLayer.remove();
        shadeLayer = L.imageOverlay(shadeUrls[shadeIdx], shadeBbox, {opacity: .9})
        shadeLayer.addTo(map);
        console.log('Updated shade map to idx: ' + shadeIdx.toString() + ", url: " + shadeUrls[shadeIdx]); 
    };

    // // listen to click events to show a popup window
    // // the content of the popup is plain html
    // // this is a nice example how function chaining is possible with Leaflet
    // map.on('click', function(e) {
    // var popup = L.popup()
    //     .setLatLng(e.latlng)
    //     .setContent('<p>Hello, world!</p>')
    //     .openOn(map);
    // });

});
