// SEE: https://sandbox.idre.ucla.edu/sandbox/general/zoomable-image-with-gdal-and-leaflet

// init - run on page load
$(document).ready(function() {
    
//     var map = L.map('parasol-map').setView([51.505, -0.09], 13);

//     L.tileLayer('https://api.tiles.mapbox.com/v4/{id}/{z}/{x}/{y}.png?access_token={accessToken}', {
//         attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors, <a href="https://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, Imagery © <a href="https://www.mapbox.com/">Mapbox</a>',
//         maxZoom: 18,
//         id: 'mapbox.streets',
//         accessToken: 'pk.eyJ1Ijoia2VpdGhmbWEiLCJhIjoiY2ppZWloODY3MGtoZDNrcndrejgwNDRsZCJ9.LY7xuFqBMX-B6DEoy75sLQ',
//     }).addTo(pmap);

    var map = L.map('parasol-map', {
        maxZoom: 0,
        minZoom: 6,
        crs: L.CRS.Simple
    }).setView([40.75, -74.18], 0);

    var imageUrl = 'http://www.lib.utexas.edu/maps/historical/newark_nj_1922.jpg',
        imageBounds = [[40.712216, -74.22655], [40.773941, -74.12544]];
    L.imageOverlay(imageUrl, imageBounds).addTo(map);


    //var imageUrl = 'top.png';
    //var imageBounds = [[42.3343660, -71.0825971], [42.3620201, -71.0453125]];
    //L.imageOverlay(imageUrl, imageBounds).addTo(map);

    console.log(map);

});
