var map;
var lgpx;

var marker;

function dataReady() {
	map.zoomToExtent(lgpx.getDataExtent());
}

function initMap() {

	map = new OpenLayers.Map ("map", {
		controls:[
			new OpenLayers.Control.Navigation(),
			new OpenLayers.Control.PanZoomBar(),
			new OpenLayers.Control.LayerSwitcher()
			],
		maxExtent: new OpenLayers.Bounds(-20037508.34,-20037508.34,20037508.34,20037508.34),
		maxResolution: 156543.0399,
		numZoomLevels: 19,
		units: 'm',
		projection: new OpenLayers.Projection("EPSG:900913"),
		displayProjection: new OpenLayers.Projection("EPSG:4326")
	});

	layerMapnik = new OpenLayers.Layer.OSM.Mapnik("Default");
	map.addLayer(layerMapnik);
	layerCycleMap = new OpenLayers.Layer.OSM.CycleMap("Cycle Map");
	map.addLayer(layerCycleMap);
	layerMarkers = new OpenLayers.Layer.Markers("Markers");
	map.addLayer(layerMarkers);

	lgpx = new OpenLayers.Layer.GML("Track", "light.gpx", {
		format: OpenLayers.Format.GPX,
		style: {strokeColor: "#9600ff", strokeWidth: 5, strokeOpacity: 0.5},
		projection: new OpenLayers.Projection("EPSG:4326"),
		eventListeners: { 'loadend': dataReady }
	});

	map.addLayer(lgpx);

	lgpx.loadGML();

	var size = new OpenLayers.Size(32,32);
	var offset = new OpenLayers.Pixel(-size.w/2, -size.h/2);
	var icon = new OpenLayers.Icon('../images/crosshair.png',size,offset);
	marker = new OpenLayers.Marker(new OpenLayers.LonLat(positionIndex[0][1], positionIndex[0][0]).transform(new OpenLayers.Projection("EPSG:4326"), map.getProjectionObject()),icon);
	layerMarkers.addMarker(marker);

	$('graphAltitude').addEvent('mousemove', graphAltitudeMouseMove);
	$('graphSpeed').addEvent('mousemove', graphSpeedMouseMove);
	$('graphCadence').addEvent('mousemove', graphCadenceMouseMove);
	$('graphHR').addEvent('mousemove', graphHRMouseMove);
}

function graphAltitudeMouseMove(event) {
	graphMouseMove(event, 'graphAltitude');
}

function graphSpeedMouseMove(event) {
	graphMouseMove(event, 'graphSpeed');
}

function graphCadenceMouseMove(event) {
	graphMouseMove(event, 'graphCadence');
}

function graphHRMouseMove(event) {
	graphMouseMove(event, 'graphHR');
}

function graphMouseMove(event, graph) {
	var p = $(graph).getPosition();
	var x = event.page.x - p.x

	/* HACKHACKHACK */
	x -= 59

	if( x >= 0 && x < positionIndex.length ) {
		marker.moveTo(map.getLayerPxFromLonLat(new OpenLayers.LonLat(positionIndex[x][1], positionIndex[x][0]).transform(new OpenLayers.Projection("EPSG:4326"), map.getProjectionObject())));
	}
}

window.addEvent('domready', function() {
	initMap();
});

