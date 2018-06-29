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
            draggable: true,
        },
        searchLabel: text,
        retainZoomLevel: true,
        autoClose: true,
        keepResult: true,
    }); 
    return search
}


// define custom slider control
// see: https://github.com/Eclipse1979/leaflet-slider
L.Control.Slider = L.Control.extend({
    options: {
        position: 'bottomright',
        min: 0,
        max: 250,
        step: 1,
        value: 50,
        inputCallback: function(value) {
            console.log(value);
        }
    },
    initialize: function (options) {
        L.setOptions(this, options);
    },
    onAdd: function (map) {
        this.container = L.DomUtil.create('div', 'leaflet-slider-container');
        this.slider = L.DomUtil.create('input', 'leaflet-slider', this.container);
        this.slider.setAttribute("type", "range");
        this.slider.setAttribute("min", this.options.min);
        this.slider.setAttribute("max", this.options.max);
        this.slider.setAttribute("step", this.options.step);
        this.slider.setAttribute("value", this.options.value);
        L.DomEvent.on(this.slider, "input", function (e) {
            this.options.inputCallback(this.slider.value);
        }, this);
        L.DomEvent.disableClickPropagation(this.container);
        return this.container;
    }
});


// TODO: use beta value from the slider, when it exists
function updateRoute(event) {
        
    // find marker locations
    var pts = []
    map.eachLayer(function(lyr) {
        if (lyr instanceof L.Marker) {
            pts.push(lyr.getLatLng());
        }
    });

    if (pts.length == 2) {
        // get route from backend and display route
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
    } else {
        // not enough points, clear route
        if (route) route.remove();
    }
}


window.onload = function () {

    // create map
    map = L.map('map', {
        center: [42.3481931, -71.0639548],
        zoom: 15,
        zoomControl: false
    });

    // add zoom control
    new L.Control.Zoom({
        position: 'bottomleft' 
    }).addTo(map);

    // add OSM basemap
    L.tileLayer('https://api.tiles.mapbox.com/v4/{id}/{z}/{x}/{y}.png?access_token=pk.eyJ1IjoibWFwYm94IiwiYSI6ImNpejY4NXVycTA2emYycXBndHRqcmZ3N3gifQ.rJcFIG214AriISLbB6B5aw', {
        maxZoom: 18,
        attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors, ' +
            '<a href="https://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>',
        id: 'mapbox.streets'
    }).addTo(map);

    // add origin and destination search bars
    searchProvider = new OpenStreetMapProvider();
    originSearch = newSearchControl("Enter origin address", greenIcon);
    destSearch = newSearchControl("Enter destination address", greenIcon);
    map.addControl(originSearch); 
    map.addControl(destSearch); 
    map.on('geosearch/showlocation', updateRoute);
    map.on('geosearch/marker/dragend', updateRoute);

    // update route when search bar "x" is clicked
    var resetBtns = document.getElementsByClassName("reset");
    for (var ii = 0; ii < resetBtns.length; ii++) {
        resetBtns[ii].addEventListener('click', updateRoute, false);
    }

    // add sun/shade preference slider
    var slider = new L.Control.Slider({
        min: 0,
        max: 1,
        step: 0.01,
        value: 0.5,
        inputCallback: function(val) {
            beta = val;
            console.log('Beta updated to: ', beta);
        }
    });
    map.addControl(slider);

};
