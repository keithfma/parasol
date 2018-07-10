var GeoSearchControl = window.GeoSearch.GeoSearchControl;
var OpenStreetMapProvider = window.GeoSearch.OpenStreetMapProvider;
var map;
var searchProvider;
var originSearch;
var destSearch;
var optimalRoute;
var optimalRouteLength;
var optimalRouteSun;
var shortestRoute;
var shortestRouteLength;
var shortestRouteSun;
var beta=0.5;
var shadeLayers;
var shadeLayer;
var routePopup;


// see: https://github.com/pointhi/leaflet-color-markers 
var endptIcon = new L.DivIcon.SVGIcon({
    circleRatio: 0.3,
    color: "#6b5b95",
    fillOpacity: 0.9
});


// see: https://github.com/smeijer/leaflet-geosearch
function newSearchControl(text) {
    const search = new GeoSearchControl({
        provider: searchProvider,
        style: "bar",
        autoClose: false,
        showMarker: true,
        marker: {
            icon: endptIcon,
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
        max: 1,
        step: 0.01,
        value: 0.5,
    },
    initialize: function (options) {
        L.setOptions(this, options);
    },
    onAdd: function (map) {
        this.container = L.DomUtil.create('div');
        this.leftIcon = L.DomUtil.create('img', 'slider-icon', this.container);
        this.leftIcon.setAttribute('src', '/static/sun.png');
        this.leftIcon.setAttribute('width', '15px');
        this.slider = L.DomUtil.create('input', 'slider', this.container);
        this.slider.setAttribute("type", "range");
        this.slider.setAttribute("min", this.options.min);
        this.slider.setAttribute("max", this.options.max);
        this.slider.setAttribute("step", this.options.step);
        this.slider.setAttribute("value", this.options.value);
        L.DomEvent.on(this.slider, "change", function (e) {
            beta = parseFloat(this.slider.value);
            console.log('Beta updated to: ', beta);
            updateOptimalRoute();
        }, this);
        L.DomEvent.disableClickPropagation(this.slider);
        this.leftIcon = L.DomUtil.create('img', 'slider-icon', this.container);
        this.leftIcon.setAttribute('src', '/static/sun.png');
        this.leftIcon.setAttribute('width', '25px');
        return this.container;
    }
});


// define custom toggle button control
L.Control.Toggle = L.Control.extend({
    options: {
        imgSrc: '/static/sun.png',
        imgWidth: '20px',
        position: 'bottomleft' 
    },
    initialize: function (options) {
        L.setOptions(this, options);
    },
    onAdd: function (map) {
        this.toggle = L.DomUtil.create('input', 'toggle');
        this.toggle.setAttribute("type", "image");
        this.toggle.setAttribute("src", this.options.imgSrc);
        this.toggle.setAttribute("width", this.options.imgWidth);
        L.DomEvent.on(this.toggle, "click", function (e) {
            var isDown = e.target.classList.contains('toggle-down');
            if (isDown) {
                e.target.classList.remove('toggle-down');
                shadeLayer._container.classList.add('hidden');
            } else {
                e.target.classList.add('toggle-down');
                shadeLayer._container.classList.remove('hidden');
            }
        }, this);
        L.DomEvent.disableClickPropagation(this.toggle);
        return this.toggle;
    }
});


// define custom time input control
L.Control.Time = L.Control.extend({
    options: {
        optList: [],      // must be set
        defaultIdx: null, // must be set
        position: 'bottomleft',
    },
    initialize: function (options) {
        L.setOptions(this, options);
    },
    onAdd: function (map) {
        this.time = L.DomUtil.create('select', 'time');
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
            updateAllRoutes();
        }, this);
        L.DomEvent.disableClickPropagation(this.time);
        return this.time;
    }
});


// return selected time as {hour: xx, minute: xx}
function selectedTime() {
    var idx = parseInt(document.getElementsByClassName('time')[0].value);
    var txt = layerTimes[idx];
    var txt_parts = txt.split(':');
    return {hour: parseInt(txt_parts[0]), minute: parseInt(txt_parts[1])};
}


// return location of (up to 2) endpoint markers
function selectedEndpts() {
    var pts = []
    map.eachLayer(function(lyr) {
        if (lyr instanceof L.Marker) {
            pts.push(lyr.getLatLng());
        }
    });
    return pts;
}


// call server to compute optimal route and display result
function updateOptimalRoute() {
        
    pts = selectedEndpts();
    now = selectedTime();

    if (pts.length == 2) { // get route from backend, store metadata, display route
        $.ajax({
            url: '/route/optimal',
            type: 'get',
            data: {lat0: pts[0].lat, lon0: pts[0].lng, lat1: pts[1].lat, lon1: pts[1].lng,
                   beta: beta, hour: now.hour, minute: now.minute},
            dataType: 'json',
            error: function(result) {
		if (result.status == 403) { // endpoint out-of-bounds
	            alert("One or more endpoint is outside the Parasol domain. Please try again.");
	        } else {
                    console.log('Failed to fetch route, result:', result);
	        }
	    },
            success: function(result) {
                optimalRouteLength = result.length;
                optimalRouteSun = result.sun;
                if (optimalRoute) {
                    optimalRoute.remove();
                    map.almostOver.removeLayer(optimalRoute);
                }
                optimalRoute = L.geoJSON(result.route, {style: {color: "#6b5b95", weight: 5}});
                optimalRoute.addTo(map);
                map.almostOver.addLayer(optimalRoute);
            }
        });
    } else { // not enough points, clear route
        if (optimalRoute) {
            map.almostOver.removeLayer(optimalRoute);
            optimalRoute.remove();
        }
    }
}


// call server to compute shortest route, but do not display
function updateShortestRoute() {
        
    pts = selectedEndpts();
    now = selectedTime();

    if (pts.length == 2) { // get route from backend, store metadata, display route
        $.ajax({
            url: '/route/shortest',
            type: 'get',
            data: {lat0: pts[0].lat, lon0: pts[0].lng, lat1: pts[1].lat, lon1: pts[1].lng,
                   hour: now.hour, minute: now.minute},
            dataType: 'json',
            error: function(result) {console.log('Failed to fetch route, result:', result);},
            success: function(result) {
                shortestRouteLength = result.length;
                shortestRouteSun = result.sun;
            }
        });
    }
}


function updateAllRoutes() {
    updateShortestRoute();
    updateOptimalRoute();
}


// add/replace shade layer
function updateShade() {
    var layerSelect = document.getElementsByClassName('time')[0];
    var meta = shadeLayers[parseInt(layerSelect.value)];
    if (shadeLayer) shadeLayer.remove();
    shadeLayer = L.tileLayer.wms(meta.url, meta.params).addTo(map);
    var toggle = document.getElementsByClassName('toggle')[0];
    if (!toggle.classList.contains('toggle-down')) {
        shadeLayer._container.classList.add('hidden');
    }
}


// generate contents for route popup
function popupHtml() {
    if (optimalRoute) {
        html = 'Length: ' + optimalRouteLength.toFixed(0) + 'm';
        html += '<br>' + (optimalRouteLength/shortestRouteLength).toFixed(2) + 'x length' ;
        html += '<br>' + (optimalRouteSun/shortestRouteSun).toFixed(2) + 'x sun';
    } else {
        html = '';
    }
    return html
}


window.onload = function () {

    // create map
    map = L.map('map', {
        center: [42.3481931, -71.0639548],
        zoom: 15,
        zoomControl: false,
        attributionControl: false
    });

    // enable tooltips when user (nearly) hovers over routes
    map.on('almost:click', function (e) {
        if (routePopup) {
            map.removeLayer(routePopup);
            routePopup = null;
        } else { 
            routePopup = L.popup().setLatLng(e.latlng).setContent(popupHtml).openOn(map);
        }
    });

    // add search bars
    searchProvider = new OpenStreetMapProvider();
    originSearch = newSearchControl("Enter origin address");
    destSearch = newSearchControl("Enter destination address");
    map.addControl(originSearch); 
    map.addControl(destSearch); 
    map.on('geosearch/showlocation', updateAllRoutes);
    map.on('geosearch/marker/dragend', updateAllRoutes);

    // update route when search bar "x" is clicked
    var resetBtns = document.getElementsByClassName("reset");
    for (var ii = 0; ii < resetBtns.length; ii++) {
        resetBtns[ii].addEventListener('click', updateAllRoutes, false);
    }

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

            // add bottom controls
            new L.Control.Slider({position: 'bottomleft'}).addTo(map);
            new L.Control.Time({position: 'bottomleft', optList: layerTimes, defaultIdx: bestIdx}).addTo(map);
            new L.Control.Toggle({position: 'bottomleft'}).addTo(map);
            new L.Control.Zoom({position: 'bottomleft'}).addTo(map);
            
            // init shade layer
            updateShade(); 
        }
    });

};
