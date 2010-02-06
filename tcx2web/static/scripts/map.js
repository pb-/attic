var map;
var lgpx;

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

	lgpx = new OpenLayers.Layer.GML("Track", "light.gpx", {
		format: OpenLayers.Format.GPX,
		style: {strokeColor: "#9600ff", strokeWidth: 5, strokeOpacity: 0.5},
		projection: new OpenLayers.Projection("EPSG:4326"),
		eventListeners: { 'loadend': dataReady }
	});

	map.addLayer(lgpx);

	lgpx.loadGML();

	$('graphAltitude').addEvent('mousemove', graphMouseMove);
	$('graphSpeed').addEvent('mousemove', graphMouseMove);
	$('graphCadence').addEvent('mousemove', graphMouseMove);
}

function graphMouseMove(event) {
	alert('move!');
}

window.addEvent('domready', function() {
	initMap();
});
