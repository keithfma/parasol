var GeoSearchControl = window.GeoSearch.GeoSearchControl;
var OpenStreetMapProvider = window.GeoSearch.OpenStreetMapProvider;
var map;
var searchProvider;
var originSearch;
var destSearch;
var route;
var beta;


// see: https://github.com/pointhi/leaflet-color-markers 
var greenIcon = new L.Icon({
    iconUrl: 'https://cdn.rawgit.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
});


// see: https://github.com/smeijer/leaflet-geosearch
function newSearchControl(text, icon) {
    const search = new GeoSearchControl({
        provider: searchProvider,
        style: "bar",
        autoClose: false,
        showMarker: true,
        marker: {
            icon: icon,
            draggable: false,
        },
        searchLabel: text,
        retainZoomLevel: true,
        autoClose: true,
        keepResult: true
    }); 
    return search
}


function updateBeta(value) {
    beta = value;
    console.log('Beta updated to: ', beta);
}


// TODO: use beta value from the slider, when it exists
function updateRoute(event) {
    // find marker locations
    var pts = []
    map.eachLayer(function(lyr) {
        if (lyr instanceof L.Marker) {
            pts.push(lyr.getLatLng());
        }
    });
    console.log(pts);
    // get route from backend and display route
    if (pts.length == 2) {
        $.ajax({
            url: '/route',
            type: 'get',
            data: {
                lat0: pts[0].lat,
                lon0: pts[0].lng, 
                lat1: pts[1].lat,
                lon1: pts[1].lng,
                beta: beta
            },
            dataType: 'json',
            error: function(result) {
                console.log('Failed to fetch route, result:', result);
            },
            success: function(result) {
                console.log('Successfully fetched route, result:', result);
                if (route) route.remove();
                route = L.geoJSON(result, { 
                    style: { 
                        "color": "#33B028",
                        "weight": 5,
                        "opacity": 0.8
                    }
                });
                route.addTo(map);
            }
        });
    }
}


window.onload = function () {

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
            '<a href="https://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>',
        id: 'mapbox.streets'
    }).addTo(map);

    searchProvider = new OpenStreetMapProvider();

    originSearch = newSearchControl(
        "Enter origin address",
        greenIcon);
    map.addControl(originSearch); 

    destSearch = newSearchControl(
        "Enter destination address",
        greenIcon);
    map.addControl(destSearch); 

    map.on('geosearch/showlocation', updateRoute);

    L.control.slider(updateBeta, {
        id: "beta-slider", 
        orientation: 'horizontal',
        postion: 'bottomright',
        min: 0,
        max: 1,
        step: 0.01,
        value: 0.5,
        collapsed: false,
        size: "90%",
        showValue: false,
    }).addTo(map);

};
