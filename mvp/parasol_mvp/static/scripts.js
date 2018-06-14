
// init - run on page load
$(document).ready(function() {
    var pmap = L.map('parasol-map').setView([51.505, -0.09], 13);
    L.tileLayer('https://api.tiles.mapbox.com/v4/{id}/{z}/{x}/{y}.png?access_token={accessToken}', {
        attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors, <a href="https://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, Imagery © <a href="https://www.mapbox.com/">Mapbox</a>',
        maxZoom: 18,
        id: 'mapbox.streets',
        accessToken: 'pk.eyJ1Ijoia2VpdGhmbWEiLCJhIjoiY2ppZWloODY3MGtoZDNrcndrejgwNDRsZCJ9.LY7xuFqBMX-B6DEoy75sLQ',
    }).addTo(pmap);
});
