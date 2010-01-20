import xml.dom.minidom
import datetime
import os
import errno
import pickle

import sys
sys.path.append('/home/dp/code/python/pydataplot')
import dataplot


def unknown_date_format(s):
	# %Y-%m-%dT%H:%M:%SZ
	# 2010-01-16T13:09:29Z
	# 01234567890123456789

#	class utc(datetime.tzinfo):
#		def utcoffset(self, dt):
#			return datetime.timedelta()

	u = datetime.datetime.strptime(s, '%Y-%m-%dT%H:%M:%SZ')
#	t = datetime.datetime(u.year, u.month, u.day, u.hour, u.minute, u.second, 0, utc())

	return u

def htmlCourse(course):
	html = """
<!doctype html>
<html>
  <head>
   <meta http-equiv="Content-type" content="text/html;charset=UTF-8">
   <title>Ride &quot;%s&quot;</title>
   <script src="http://www.openlayers.org/api/OpenLayers.js"></script>
   <script src="http://www.openstreetmap.org/openlayers/OpenStreetMap.js"></script>
   <script type="text/javascript">
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

   </script>
   <style type="text/css">
    body {
     width: 900px;
     margin: auto;
	}
    #map {
     width: 500px;
	 height: 400px;
	 float: right;
	 border: 1px solid black;
    }
    #meta {
     float: left;
	 width: 20em;
    }
	#graphs {
	 padding-top: 3em;
	 clear: both;
	 list-style: none;
	}
	#graphs li h3 {
	 font-size: 90%%;
	 text-align: center;
	 padding: 0;
	 margin: 5px;
    }
   </style>
  </head>
 <body onload="init();">""" % course.id

 	html += '<h1>%s</h1>' % course.id


	html += '<table id="meta">'
	html += '<tr><td>Start</td><td>%s</td></tr>' % str(course.start)
	html += '<tr><td>End</td><td>%s</td></tr>' % str(course.end)
	dur = (course.end - course.start).seconds
	html += '<tr><td>Duration</td><td>%02d:%02d:%02d</td></tr>' % (dur / 3600, dur % 3600 / 60, dur % 60)
	html += '<tr><td>Distance</td><td>%.1f km</td></tr>' % (course.dist / 1000)
	html += '<tr><td>Total ascent</td><td>%d m</td></tr>' % (course.asc)
	html += '<tr><td>v<sub>avg</sub></td><td>%.1f km/h</td></tr>' % (3.6 * course.dist / dur)
	html += '<tr><td>v<sub>max</sub></td><td>%.1f km/h</td></tr>' % (3.6 * course.vmax)
	html += '<tr><td>Calories</td><td>%d</td></tr>' % course.calories
	html += '<tr><td>Cadence<sub>avg</sub></td><td>%d</td></tr>' % course.cadence
	html += '<tr><td></td><td></td></tr>'
	html += '<tr><td>GPX download</td><td><a href="light.gpx">light.gpx</a></td></tr>'
	html += '</table>'

	html += '<div id="map"></div>'

	html += '<ul id="graphs"><li><h3>Altitude</h3><img src="altitude.png" alt="Altitude"></li><li><h3>Speed</h3><img src="speed.png" alt="Speed"></li><li><h3>Cadence</h3><img src="cadence.png" alt="Cadence"></li></ul>'

	html += '</body></html>'
	return html

def writeCourse(course):
	dirname = '%d-%02d-%02d--%02d%02d' % (course.start.year, course.start.month, course.start.day, course.start.hour, course.start.minute)

	try:
		os.mkdir(dirname)
	except OSError as e:
		if e.errno == errno.EEXIST:
			pass
		else:
			raise
	
	# prepare data samples for plot
	width = 800

	interval = course.dist / width
	pi = 0 # point index

	samplesAlt = []
	samplesSpeed = []
	samplesCad = []

	for i in range(width):
		position = i * interval + interval/2

		try:
			while not course.trackpoints[pi + 1].dist >= position:
				pi += 1
		except IndexError:
			print 'warning: could only obtain %d of %d samples' % (i,width)
			break

		samplesAlt.append((position / 1000, course.trackpoints[pi].alt))

		if course.trackpoints[pi].cad:
			samplesCad.append((position / 1000, course.trackpoints[pi].cad))
		else:
			samplesCad.append((position / 1000, 0))

		if (pi+1) < len(course.trackpoints):
			deltaDist = course.trackpoints[pi+1].dist - course.trackpoints[pi].dist
			deltaTime = (course.trackpoints[pi+1].time - course.trackpoints[pi].time).seconds

			samplesSpeed.append((position / 1000, 3.6 * deltaDist / deltaTime))
	

	# render plots
	plotter = dataplot.Plotter()
	cfg = dataplot.PlotConfig()

	cfg.dim.type = cfg.dim.SIZE_PLANE
	cfg.dim.width = width
	cfg.dim.height = 120
	cfg.renderArea = True
	cfg.label.x = 'Distance [km]'
	cfg.grid = True


	cfg.label.y = 'Altitude [m]'
	cfg.color.graph = (0x8f,0xaa,0x1e)
	cfg.color.area = (0xdf,0xe7,0xbf)
	plot = plotter.plotPoints(samplesAlt, cfg)
	plot.writePng(os.path.join(dirname, 'altitude.png'))
	
	cfg.label.y = 'Speed [km/h]'
	cfg.color.graph = (0x27,0x82,0xf7)
	cfg.color.area = (0xc2,0xdc,0xfd)
	plot = plotter.plotPoints(samplesSpeed, cfg)
	plot.writePng(os.path.join(dirname, 'speed.png'))
	
	cfg.label.y = 'Cadence [rpm]'
	cfg.color.graph = (0xb8,0x4f,0)
	cfg.color.area = (0xeb,0xcd,0xb7)
	plot = plotter.plotPoints(samplesCad, cfg)
	plot.writePng(os.path.join(dirname, 'cadence.png'))


	# gpx file with all points (invalid)
	f = open(os.path.join(dirname, 'full.gpx'), 'w')
	f.write('<gpx><trk><trkseg>')
	for p in course.trackpoints:
		if p.lat and p.lon:
			f.write('<trkpt lat="%f" lon="%f"/>' % (p.lat,p.lon))
	f.write('</trkseg></trk></gpx>')
	f.close()

	# lightweight gpx file (valid)   gpsbabel -i gpx -f full.gpx -x simplify,error=0.005k -o gpx -F light.gpx
	os.system('gpsbabel -i gpx -f %s -x simplify,error=0.005k -o gpx -F %s' % (os.path.join(dirname, 'full.gpx'), os.path.join(dirname, 'light.gpx')))

	# create index file
	f = open(os.path.join(dirname, 'index.html'), 'w')
	f.write(htmlCourse(course))
	f.close()


	# save metadata
	course.trackpoints = None
	f = open(os.path.join(dirname, 'meta.pickle'), 'w')
	pickle.dump(course, f)
	f.close()


class Trackpoint:
	def __init__(self, time, lat, lon, alt, dist, cad, hr):
		self.time = time
		self.lat = lat
		self.lon = lon
		self.alt = alt
		self.dist = dist
		self.cad = cad
		self.hr = hr


class Course:
	def __init__(self, id, start, time, dist, vmax, calories, cadence):
		self.id = id
		self.start = start
		self.time = time
		self.dist = dist
		self.vmax = vmax
		self.calories = calories
		self.cadence = cadence

		self.trackpoints = []
		self.asc = 0
		self.end = None


def firstChild(node, name):
	return node.getElementsByTagName(name)[0]

def simpleVal(node, name):
	return get_text(firstChild(node,name).childNodes)

def get_text(nodes):
	rc = ''

	for node in nodes:
		if node.nodeType == node.TEXT_NODE:
			rc += node.data

	return rc.strip()

class TcxParser:

	def get_text(self, nodes):
		rc = ''

		for node in nodes:
			if node.nodeType == node.TEXT_NODE:
				rc += node.data

		return rc.strip()

	def parse(self, data):
		self.dom = xml.dom.minidom.parse(data)

		acts = self.dom.getElementsByTagName('Activities')[0]
		act = acts.getElementsByTagName('Activity')[0]
		id = self.get_text(act.getElementsByTagName('Id')[0].childNodes)

		lap = act.getElementsByTagName('Lap')[0]

		start = unknown_date_format(lap.attributes.item(0).value)

		time = float(self.get_text(lap.getElementsByTagName('TotalTimeSeconds')[0].childNodes))
		dist = float(self.get_text(lap.getElementsByTagName('DistanceMeters')[0].childNodes))
		vmax = float(self.get_text(lap.getElementsByTagName('MaximumSpeed')[0].childNodes))
		calories = int(self.get_text(lap.getElementsByTagName('Calories')[0].childNodes))
		cad = int(self.get_text(lap.getElementsByTagName('Cadence')[0].childNodes))

		course = Course(id, start, time, dist, vmax, calories, cad)

		tracks = lap.getElementsByTagName('Track')
		for track in tracks:
			trackpoints = track.getElementsByTagName('Trackpoint')

			for tp in trackpoints:
				time = unknown_date_format(self.get_text(tp.getElementsByTagName('Time')[0].childNodes))

				positions = tp.getElementsByTagName('Position')
				if len(positions) > 0:
					pos = positions[0]
					lat = float(simpleVal(pos, 'LatitudeDegrees'))
					lon = float(simpleVal(pos, 'LongitudeDegrees'))
				else:
					lat = None
					lon = None

				alt = float(simpleVal(tp, 'AltitudeMeters'))
				dist = float(simpleVal(tp, 'DistanceMeters'))

				cadences = tp.getElementsByTagName('Cadence')
				if len(cadences) > 0:
					cadence = int(simpleVal(tp, 'Cadence'))
				else:
					cadence = None

				t = Trackpoint(time, lat, lon, alt, dist, cadence, 0)

				course.trackpoints.append(t)
				course.end = time
				if len(course.trackpoints) > 1:
					if course.trackpoints[-1].alt > course.trackpoints[-2].alt:
						course.asc += course.trackpoints[-1].alt - course.trackpoints[-2].alt


		return course
	


			

		

p = TcxParser()

course = p.parse(sys.argv[1])
writeCourse(course)


