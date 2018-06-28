var GeoSearchControl = window.GeoSearch.GeoSearchControl;
var OpenStreetMapProvider = window.GeoSearch.OpenStreetMapProvider;
var map;
var startSearch;
var destSearch;

var greenIcon = new L.Icon({
    iconUrl: 'https://cdn.rawgit.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
});

var blueIcon = new L.Icon({
    iconUrl: 'https://cdn.rawgit.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
});

function newSearchControl(text, icon) {
    const search = new GeoSearchControl({
        provider: new OpenStreetMapProvider(),
        style: "bar",
        autoClose: false,
        showMarker: true,
        marker: {
            icon: icon,
            draggable: false,
        },
        searchLabel: text
    }); 
    return search
}

window.onload = function () {

    // init the map object
    map = L.map('map', {
        center: [42.3481931, -71.0639548],
        zoom: 15,
        zoomControl: false
    });

    new L.Control.Zoom({
        position: 'bottomleft' 
    }).addTo(map);

    L.tileLayer('https://api.tiles.mapbox.com/v4/{id}/{z}/{x}/{y}.png?access_token=pk.eyJ1IjoibWFwYm94IiwiYSI6ImNpejY4NXVycTA2emYycXBndHRqcmZ3N3gifQ.rJcFIG214AriISLbB6B5aw', {
        maxZoom: 18,
        attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors, ' +
            '<a href="https://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, ' +
            'Imagery © <a href="https://www.mapbox.com/">Mapbox</a>',
        id: 'mapbox.streets'
    }).addTo(map);

    originSearch = newSearchControl(
        "Enter origin address",
        greenIcon);
    map.addControl(originSearch); 

    destSearch = newSearchControl(
        "Enter destination address",
        greenIcon);
    map.addControl(destSearch); 

};
