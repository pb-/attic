
/*		var lat=50.2309
		var lon=8.879
		var zoom=13*/

		var map;
		var lgpx;

		function dataReady() {
			map.zoomToExtent(lgpx.getDataExtent());
		}

		function init() {

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
			} );
			layerMapnik = new OpenLayers.Layer.OSM.Mapnik("Mapnik");
			map.addLayer(layerMapnik);
			layerCycleMap = new OpenLayers.Layer.OSM.CycleMap("CycleMap");
			map.addLayer(layerCycleMap);

                        lgpx = new OpenLayers.Layer.GML("Track", "light.gpx", {
                            format: OpenLayers.Format.GPX,
                            style: {strokeColor: "#9600ff", strokeWidth: 5, strokeOpacity: 0.5},
                            projection: new OpenLayers.Projection("EPSG:4326"),
							eventListeners: { 'loadend': dataReady }
                        });
                        map.addLayer(lgpx);

			lgpx.loadGML()
//			map.zoomToExtent(lgpx.getDataExtent());
 
		//	var lonLat = new OpenLayers.LonLat(lon, lat).transform(new OpenLayers.Projection("EPSG:4326"), map.getProjectionObject());
		//	map.setCenter (lonLat, zoom);
		}

