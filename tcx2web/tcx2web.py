import sys
import os
import datetime
import errno
import pickle
import xml.sax
import xml.sax.handler

import dp
import dataplot
import gpx

def parseIsoDateFormat(s):
	# FIXME this is utc, convert to localtime
	u = datetime.datetime.strptime(s, '%Y-%m-%dT%H:%M:%SZ')
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
   <script src="../scripts/map.js"></script>
   <link rel="stylesheet" href="../styles/ride.css" type="text/css" media="screen">
  </head>
 <body onload="init();">""" % course.id

 	html += '<h1>%s</h1>' % course.id

	html += '<p><a href="../">All rides</a></p>'
	html += '<table id="meta">'
	html += '<tr><td>Start</td><td>%s</td></tr>' % str(course.start)
	html += '<tr><td>End</td><td>%s</td></tr>' % str(course.end)
	dur = (course.end - course.start).seconds
	html += '<tr><td>Duration</td><td>%02d:%02d:%02d</td></tr>' % (dur / 3600, dur % 3600 / 60, dur % 60)
	html += '<tr><td>Distance</td><td>%.1f km</td></tr>' % (course.dist / 1000)
	html += '<tr><td>Total ascent</td><td>%d m</td></tr>' % (course.asc)
	html += '<tr><td>v<sub>avg</sub></td><td>%.1f km/h</td></tr>' % (3.6 * course.dist / dur)
	if course.vmax:
		html += '<tr><td>v<sub>max</sub></td><td>%.1f km/h</td></tr>' % (3.6 * course.vmax)
	if course.calories > 0:
		html += '<tr><td>Calories</td><td>%d</td></tr>' % course.calories
	if course.cadence:
		html += '<tr><td>Cadence<sub>avg</sub></td><td>%d</td></tr>' % course.cadence
	html += '<tr><td></td><td></td></tr>'
	html += '<tr><td>GPX download</td><td><a href="light.gpx">light.gpx</a></td></tr>'
	html += '</table>'

	html += '<div id="map"></div>'

#	html += '<ul id="graphs"><li><h3>Altitude</h3><img src="altitude.png" alt="Altitude"></li><li><h3>Speed</h3><img src="speed.png" alt="Speed"></li><li><h3>Cadence</h3><img src="cadence.png" alt="Cadence"></li></ul>'
	html += '<ul id="graphs"><li><img src="altitude.png" alt="Altitude"></li><li><img src="speed.png" alt="Speed"></li><li><img src="cadence.png" alt="Cadence"></li></ul>'

	html += '</body></html>'
	return html

def writeIndex():

	courses = []
	dir = os.listdir('.')
	for file in dir:
		if os.path.isdir(file):
			mf = os.path.join(file, 'meta.pickle')
			if os.path.exists(mf):
				f = open(mf)
				c = pickle.load(f)
				c.dname = file
				courses.append(c)
				f.close()
	
	index = open('index.html', 'w')

	index.write('<!doctype html>\n')
	index.write('<html>')
	index.write(' <head>')
	index.write('  <title>Index of rides</title>')
	index.write('  <link rel="stylesheet" href="styles/index.css" type="text/css" media="screen">')
	index.write(' </head>')
	index.write(' <body>')
	index.write('  <h1>Index of rides</h1>')

	courses.sort(key=lambda x: x.start, reverse=True)

	for c in courses:
		index.write('<div class="course"><a href="%s/"><img src="%s/icon.png"><p>%dkm / %dm<br>%s</p></a></div>' % (c.dname, c.dname, round(c.dist / 1000), c.asc, c.start.strftime('%Y-%m-%d')))

	index.write(' </body>')
	index.write('</html>')

	index.close()


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

		if course.cadence:
			if course.trackpoints[pi].cad:
				samplesCad.append((position / 1000, course.trackpoints[pi].cad))
			else:
				samplesCad.append((position / 1000, 0))

		if (pi+1) < len(course.trackpoints):
			deltaDist = course.trackpoints[pi+1].dist - course.trackpoints[pi].dist
			deltaTime = (course.trackpoints[pi+1].time - course.trackpoints[pi].time).seconds

			v = deltaDist / deltaTime

			if not course.vmax or not v > course.vmax + 1:
				samplesSpeed.append((position / 1000, 3.6 * v))
			else:
				print 'warning: dropped bogus speed sample %.2f km/h > %.2f km/h' % (3.6 * v, 3.6 * course.vmax)

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
	
	if course.cadence:
		cfg.label.y = 'Cadence [rpm]'
		cfg.color.graph = (0xb8,0x4f,0)
		cfg.color.area = (0xeb,0xcd,0xb7)
		plot = plotter.plotPoints(samplesCad, cfg)
		plot.writePng(os.path.join(dirname, 'cadence.png'))


	# gpx file with all points
	f = open(os.path.join(dirname, 'full.gpx'), 'w')
	f.write('<gpx><trk><trkseg>')
	for p in course.trackpoints:
		if p.lat and p.lon:
			f.write('<trkpt lat="%f" lon="%f"/>' % (p.lat,p.lon))
	f.write('</trkseg></trk></gpx>')
	f.close()

	# lightweight gpx file (valid)   gpsbabel -i gpx -f full.gpx -x simplify,error=0.005k -o gpx -F light.gpx
	light = os.path.join(dirname, 'light.gpx')
	full = os.path.join(dirname, 'full.gpx')
	os.system('gpsbabel -i gpx -f %s -x simplify,error=0.005k -o gpx -F %s' % (full, light))

	# create gpx icon
	icon = os.path.join(dirname, 'icon.png')
	gpxIcon = gpx.GpxIcon()
	gpxIcon.parse(light)
	gpxIcon.render(96).writePng(icon)

	# create index file
	f = open(os.path.join(dirname, 'index.html'), 'w')
	f.write(htmlCourse(course))
	f.close()

	# save metadata
	course.trackpoints = None
	f = open(os.path.join(dirname, 'meta.pickle'), 'w')
	pickle.dump(course, f)
	f.close()

def calcTotalAscent(trackpoints):
	asc = 0

	points = []

	for p in trackpoints:
		if p.dist and p.alt:
			points.append((p.dist, p.alt))

	points = dp.simplify_points(points, 2.5)

	for i in range(len(points) - 1):
		diff = points[i+1][1] - points[i][1]
		if diff > 0:
			asc += diff

	return asc


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


class TcxParser(xml.sax.handler.ContentHandler):
	def __init__(self):
		self.handlers = dict()
		for attr in dir(self):
			if attr.startswith('handle') and (attr.endswith('Start') or attr.endswith('End')):
				if callable(getattr(self, attr)):
					self.handlers[attr] = getattr(self, attr)

	
	def parse(self, filename):
		xml.sax.parse(filename, self)
		return self.course
			
	def startElement(self, element, attrs):
		name = 'handle' + element + 'Start'

		try:
			self.handlers[name](attrs)
		except KeyError:
			pass

		self.text = ''

	def endElement(self, element):
		name = 'handle' + element + 'End'

		try:
			self.handlers[name]()
		except KeyError:
			pass
	
	def characters(self, content):
		self.text += content


	########## element handlers ##############
	def handleTrainingCenterDatabaseStart(self, attrs):
		self.time = 0
		self.dist = 0
		self.vmax = None
		self.calories = 0
		self.cad = None
		self.start = None

		self.inTp = False
		self.firstLap = False
		self.trackpoints = []
	
	def handleIdEnd(self):
		self.id = self.text.strip()
	
	# Lap
	def handleLapStart(self, attrs):
		if self.firstLap:
			print '!!! warning: multiple laps, average cadence information will be bogus'
		else:
			self.start = parseIsoDateFormat(attrs.getValue('StartTime'))
			self.firstLap = True

	def handleTotalTimeSecondsEnd(self):
		self.time += float(self.text.strip())
	
	def handleDistanceMetersEnd(self):
		if self.inTp:
			self.tpdist = float(self.text.strip())
		else:
			self.dist += float(self.text.strip())
	
	def handleCaloriesEnd(self):
		self.calories += int(self.text.strip())
	
	def handleMaximumSpeedEnd(self):
		self.vmax = max(self.vmax, float(self.text.strip()))
	
	def handleCadenceEnd(self):
		if self.inTp:
			self.tpcad = int(self.text.strip())
		else:
			self.cad = int(self.text.strip())

	def handleTrainingCenterDatabaseEnd(self):
		if not self.start:
			self.start = self.trackpoints[0].time

		self.course = Course(self.id, self.start, self.time, self.dist, self.vmax, self.calories, self.cad)

		self.course.trackpoints = self.trackpoints
		self.course.end = self.course.trackpoints[-1].time

		self.course.asc = calcTotalAscent(self.course.trackpoints)

	# Trackpoint
	def handleTrackpointStart(self, attrs):
		self.tptime = None
		self.lat = None
		self.lon = None
		self.alt = None
		self.tpdist = None
		self.tpcad = None
		self.hr = None

		self.inTp = True
	
	def handleTimeEnd(self):
		self.tptime = parseIsoDateFormat(self.text.strip())
	
	def handleLatitudeDegreesEnd(self):
		self.lat = float(self.text.strip())
	
	def handleLongitudeDegreesEnd(self):
		self.lon = float(self.text.strip())
	
	def handleAltitudeMetersEnd(self):
		self.alt = float(self.text.strip())
	
	def handleTrackpointEnd(self):
		self.trackpoints.append(Trackpoint(self.tptime, self.lat, self.lon, self.alt, self.tpdist, self.tpcad, 0))

		self.inTp = False

p = TcxParser()

course = p.parse(sys.argv[1])
writeCourse(course)
writeIndex()
