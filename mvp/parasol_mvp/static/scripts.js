// SEE: https://sandbox.idre.ucla.edu/sandbox/general/zoomable-image-with-gdal-and-leaflet
// SEE: http://bl.ocks.org/bentrm/5aaedf8f2bd9361e280d

// init - run on page load
$(document).ready(function() {
    
    // init the map object
    var map = L.map('parasol-map', {
        center: [42.3481931, -71.0639548],
        zoom: 13
    });

    // we add some test layers here
    var osmAttrib = 'Map data © <a href="http://openstreetmap.org">OpenStreetMap</a> contributors';

    var osm = L.tileLayer('http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 18,
        attribution: osmAttrib
    }).addTo(map); // this will be our active base layer on startup

    // // an image overlay that will be added to the overlays of a layer switcher
    // var image = L.imageOverlay(
    //     '/img/top.png',
    //     [[42.3343660, -71.0825971], [42.3620201, -71.0453125]], {
    //     opacity: .8
    // }).addTo(map);

    // loop over 15 minute time intervals, add all layers
    for (let tt = 0; tt <= 2400; tt += 25) {
        // generate image file path
        var tstr = tt.toString().padStart(4, "0");
        var img_file = '/img/shade_' + tstr.substring(0,2) + '.' +tstr.substring(2) + '.png';
        // add image overlay
        var image = L.imageOverlay(
            img_file,
            [[42.3343660, -71.0825971], [42.3620201, -71.0453125]], {
            opacity: .8
        }).addTo(map);
    } 

    // init a map scale
    L.control.scale().addTo(map);

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
