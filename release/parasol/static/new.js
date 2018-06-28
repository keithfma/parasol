// init - run on page load
$(document).ready(function() {
    
    // init the map object
    map = L.map('map', {
        center: [42.3481931, -71.0639548],
        zoom: 15
    });

    // add basemap
    var osmAttrib = 'Map data © <a href="http://openstreetmap.org">OpenStreetMap</a> contributors';
    var osm = L.tileLayer('http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 18,
        attribution: osmAttrib
    }).addTo(map); // this will be our active base layer on startup
    
});
