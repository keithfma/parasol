var GeoSearchControl = window.GeoSearch.GeoSearchControl;
var OpenStreetMapProvider = window.GeoSearch.OpenStreetMapProvider;
var map;
var searchProvider;
var originSearch;
var destSearch;
var route;
var beta;
var shadeLayers;
var shadeLayer;


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


// define custom toggle button control
L.Control.Toggle = L.Control.extend({
    options: {
        imgSrc: null,
        imgWidth: '20px',
        position: 'bottomright'
    },
    initialize: function (options) {
        L.setOptions(this, options);
    },
    onAdd: function (map) {
        this.container = L.DomUtil.create('div', 'leaflet-toggle-container');
        this.toggle = L.DomUtil.create('input', 'leaflet-toggle', this.container);
        this.toggle.setAttribute("type", "image");
        this.toggle.setAttribute("src", this.options.imgSrc);
        this.toggle.setAttribute("width", this.options.imgWidth);
        L.DomEvent.on(this.toggle, "click", function (e) {
            var isDown = e.target.classList.contains('leaflet-toggle-down');
            if (isDown) {
                e.target.classList.remove('leaflet-toggle-down');
                shadeLayer._container.classList.add('hidden');
            } else {
                e.target.classList.add('leaflet-toggle-down');
                shadeLayer._container.classList.remove('hidden');
            }
        }, this);
        L.DomEvent.disableClickPropagation(this.container);
        return this.container;
    }
});


// define custom time input control
L.Control.Time = L.Control.extend({
    options: {
        optList: [],
        position: 'bottomright',
    },
    initialize: function (options) {
        L.setOptions(this, options);
    },
    onAdd: function (map) {
        this.container = L.DomUtil.create('div', 'leaflet-time-container');
        this.time = L.DomUtil.create('select', 'leaflet-time', this.container);
        for (let ii = 0; ii < this.options.optList.length; ii++) {
            if (ii == this.options.defaultIdx) {
                this.time.innerHTML += '<option value="' + ii + '" selected>' + this.options.optList[ii] + '</option>';
            } else {
                this.time.innerHTML += '<option value="' + ii + '">' + this.options.optList[ii] + '</option>';
            }
        }
        // callback to update shade layer
        L.DomEvent.on(this.time, "change", function (e) {
            updateShade();
        }, this);
        L.DomEvent.disableClickPropagation(this.container);
        return this.container;
    }
});


// call server to compute route and display result
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
            data: {lat0: pts[0].lat, lon0: pts[0].lng, lat1: pts[1].lat, lon1: pts[1].lng, beta: beta},
            dataType: 'json',
            error: function(result) {
                console.log('Failed to fetch route, result:', result);
            },
            success: function(result) {
                console.log('Successfully fetched route, result:', result);
                if (route) route.remove();
                route = L.geoJSON(result, { 
                    style: {color: "#33B028", weight: 5, opacity: 0.8}
                });
                route.addTo(map);
            }
        });
    } else {
        // not enough points, clear route
        if (route) route.remove();
    }
}


// add/replace shade layer
function updateShade() {
    var layerSelect = document.getElementsByClassName('leaflet-time')[0];
    var meta = shadeLayers[parseInt(layerSelect.value)];
    if (shadeLayer) shadeLayer.remove();
    shadeLayer = L.tileLayer.wms(meta.url, meta.params).addTo(map);
    var toggle = document.getElementsByClassName('leaflet-toggle')[0];
    if (!toggle.classList.contains('leaflet-toggle-down')) {
        shadeLayer._container.classList.add('hidden');
    }
}


window.onload = function () {

    // create map
    map = L.map('map', {
        center: [42.3481931, -71.0639548],
        zoom: 15,
        zoomControl: false,
        attributionControl: false
    });

    // add OSM basemap
    osm = L.tileLayer('https://api.tiles.mapbox.com/v4/{id}/{z}/{x}/{y}.png?access_token=pk.eyJ1IjoibWFwYm94IiwiYSI6ImNpejY4NXVycTA2emYycXBndHRqcmZ3N3gifQ.rJcFIG214AriISLbB6B5aw', {
        maxZoom: 18,
        id: 'mapbox.streets'
    }).addTo(map);

    // retrieve shade layer details and add related controls
    // note: all 'bottomleft' controls added here to ensure correct ordering
    $.ajax({
        url: '/layers',
        type: 'get',
        error: function(result) {
            console.log('Failed to fetch layers, result:', result);
        },
        success: function(layers) {
            // store layer metadata list
            shadeLayers = layers;
            
            // get list of layer times as formatted strings
            layerTimes = [];
            for (let ii = 0; ii < layers.length; ii++) {
                time_str = layers[ii].hour.toString().padStart(2, "0") + ':' + layers[ii].minute.toString().padStart(2, "0");
                layerTimes.push(time_str);
            }
            
            // select layer index nearest to current time
            var now = new Date();
            var nowMin = 60*now.getHours() + now.getMinutes();
            var bestDiff = 999999;
            var bestIdx = null;
            for (let ii = 0; ii < layers.length; ii++) {
                layerMin = 60*layers[ii].hour + layers[ii].minute;
                thisDiff = Math.abs(nowMin - layerMin);
                if (thisDiff < bestDiff) {
                    bestIdx = ii;
                    bestDiff = thisDiff;
                }
            }

            // add shade layer toggle
            // TODO: make these options the default, then don't include them
            new L.Control.Toggle({
                imgSrc: '/static/sun.png',
                imgWidth: '20px',
                position: 'bottomleft' 
            }).addTo(map);

            // add time input 
            new L.Control.Time({
                optList: layerTimes,
                defaultIdx: bestIdx,
                position: 'bottomleft' 
            }).addTo(map);
        
            // set initial shade layer
            updateShade(); 
            
            // add zoom control
            new L.Control.Zoom({
                position: 'bottomleft' 
            }).addTo(map);
        }
    });

    // add search bars
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
            updateRoute();
        }
    });
    map.addControl(slider);

};
