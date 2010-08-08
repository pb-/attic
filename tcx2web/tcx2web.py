#!/usr/bin/python
import sys
import os
import datetime
import errno
import shutil
import pickle
import time
import xml.sax
import xml.sax.handler
import optparse

import dp
import dataplot
import gpx

cache = {}

colors = {
	'red': '#d9182b',
	'orange': '#e8991a',
	'lightgreen': '#79af3d',
	'darkgreen': '#037746',
	'lightblue': '#0099d1',
	'darkblue': '#1c449c',
	'lightviolet': '#ae2191',
	'darkviolet': '#6b2b8c',
}

########## http://docs.python.org/library/datetime.html#tzinfo-objects #############

ZERO = datetime.timedelta(0)
HOUR = datetime.timedelta(hours=1)

STDOFFSET = datetime.timedelta(seconds = -time.timezone)
if time.daylight:
    DSTOFFSET = datetime.timedelta(seconds = -time.altzone)
else:
    DSTOFFSET = STDOFFSET

DSTDIFF = DSTOFFSET - STDOFFSET

class LocalTimezone(datetime.tzinfo):
    def utcoffset(self, dt):
        if self._isdst(dt):
            return DSTOFFSET
        else:
            return STDOFFSET

    def dst(self, dt):
        if self._isdst(dt):
            return DSTDIFF
        else:
            return ZERO

    def _isdst(self, dt):
        tt = (dt.year, dt.month, dt.day,
              dt.hour, dt.minute, dt.second,
              dt.weekday(), 0, -1)
        stamp = time.mktime(tt)
        tt = time.localtime(stamp)
        return tt.tm_isdst > 0

class UTC(datetime.tzinfo):
    def utcoffset(self, dt):
        return ZERO

    def dst(self, dt):
        return ZERO

utc = UTC()
localTimezone = LocalTimezone()

########## http://docs.python.org/library/datetime.html#tzinfo-objects #############




def parseIsoDateFormat(s):
	u = datetime.datetime.strptime(s, '%Y-%m-%dT%H:%M:%SZ')
	u = u.replace(tzinfo=utc).astimezone(localTimezone)

	return u

def mkdirp(dirname):
	try:
		os.mkdir(dirname)
	except OSError as e:
		if e.errno == errno.EEXIST:
			pass
		else:
			raise

def getTemplate(datadir, name, data):
	filename = os.path.join(datadir, 'templates', name + '.html')

	if not filename in cache:
		f = open(filename)
		cache[filename] = f.read()
		f.close()

	return cache[filename] % data


def htmlCourse(datadir, course):

	dur = (course.end - course.start).seconds

	data = {
		'id': course.id,
		'date': course.start.strftime('%B %d, %Y'),
		'start': course.start.strftime('%H:%M'),
		'end': course.end.strftime('%H:%M'),
		'duration': '%02d:%02d:%02d' % (dur / 3600, dur % 3600 / 60, dur % 60),
		'distance': course.dist / 1000,
		'climb': course.asc,
		'vavg': (3.6 * course.dist / dur),
	}

	if course.vmax:
		data['vmax'] = '<tr><td>v<sub>max</sub></td><td>%.1f km/h</td></tr>' % (3.6 * course.vmax)
	else:
		data['vmax'] = ''

	if course.calories:
		data['calories'] = '<tr><td>Calories</td><td>%d</td></tr>' % course.calories
	else:
		data['calories'] = ''
	
	if course.cadence:
		data['cadence'] = '<tr><td>Cadence<sub>avg</sub></td><td>%d</td></tr>' % course.cadence
	else:
		data['cadence'] = ''
	
	return getTemplate(datadir, 'course', data)


def writeIndex(datadir):

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

	courses.sort(key=lambda x: x.start, reverse=True)
	rides = ''

	totalDist = 0
	totalClimb = 0
	totalTime = datetime.timedelta(0)

	for c in courses:
		if hasattr(c, 'color') and c.color:
			extrastylebg = ' style="background-color: %s;"' % colors[c.color]
			extrastylebdr = ' style="border-color: %s;"' % colors[c.color]
		else:
			extrastylebg = ''
			extrastylebdr = ''

		rides += getTemplate(datadir, 'index-course', {
			'dir': c.dname,
			'dist': round(c.dist/1000),
			'climb': c.asc,
			'date': c.start.strftime('%Y-%m-%d'),
			'extrastylebg': extrastylebg,
			'extrastylebdr': extrastylebdr,
		})

		totalDist += c.dist
		totalClimb += c.asc
		totalTime += c.end - c.start


	index.write(getTemplate(datadir, 'index', {
		'rides': rides,
		'totalDist': round(totalDist/1000),
		'totalClimb': totalClimb,
		'totalTime': (totalTime.days * 24 + totalTime.seconds / 3600),
	}))

	index.close()


def writeCourse(datadir, course):
	dirname = '%d-%02d-%02d--%02d%02d' % (course.start.year, course.start.month, course.start.day, course.start.hour, course.start.minute)

	mkdirp(dirname)
	
	# prepare data samples for plot
	width = 800

	interval = course.dist / width
	pi = 0 # point index

	samplesAlt = []
	samplesSpeed = []
	samplesCad = []
	samplesHR = []
	positions = []

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

		if course.trackpoints[pi].hr:
			samplesHR.append((position / 1000, course.trackpoints[pi].hr))
		else:
			samplesHR.append((position / 1000, 0))

		if (pi+1) < len(course.trackpoints):
			deltaDist = course.trackpoints[pi+1].dist - course.trackpoints[pi].dist
			deltaTime = (course.trackpoints[pi+1].time - course.trackpoints[pi].time).seconds

			v = deltaDist / deltaTime

			if not course.vmax or not v > course.vmax + 1:
				samplesSpeed.append((position / 1000, 3.6 * v))
			else:
				print 'warning: dropped bogus speed sample %.2f km/h > %.2f km/h' % (3.6 * v, 3.6 * course.vmax)

			# position index, linear interpolation between two trackpoints
			if course.trackpoints[pi].lat and course.trackpoints[pi].lon and course.trackpoints[pi+1].lat and course.trackpoints[pi+1].lon:
				vecPos = (position - course.trackpoints[pi].dist) / deltaDist
				lat = course.trackpoints[pi].lat + (course.trackpoints[pi+1].lat - course.trackpoints[pi].lat) * vecPos
				lon = course.trackpoints[pi].lon + (course.trackpoints[pi+1].lon - course.trackpoints[pi].lon) * vecPos
				positions.append((lat,lon))
			else:
				positions.append((0,0))


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
	
	if len(samplesHR) > 0:
		cfg.label.y = 'Heart Rate [bpm]'
		cfg.color.graph = (0x96,0x0,0xff)
		cfg.color.area = (0xe6,0xc2,0xff)
		plot = plotter.plotPoints(samplesHR, cfg)
		plot.writePng(os.path.join(dirname, 'heartrate.png'))
	
	# position index
	f = open(os.path.join(dirname, 'pindex.js'), 'w')
	f.write('var positionIndex = [')
	for p in positions:
		f.write('[%.4f,%.4f],' % (p[0],p[1]))
	f.write('];')
	f.close()


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
	f.write(htmlCourse(datadir, course))
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
	
	def handleValueEnd(self):
		self.hr = int(self.text.strip())
	
	def handleTrackpointEnd(self):
		self.trackpoints.append(Trackpoint(self.tptime, self.lat, self.lon, self.alt, self.tpdist, self.tpcad, self.hr))

		self.inTp = False


op = optparse.OptionParser()
op.add_option('-c', '--color', dest='color', help='Use COLOR for the index icon')
(options, args) = op.parse_args()

if len(args) != 1:
	print 'Usage: %s [--color=COLOR] TCXFILE' % sys.argv[0]
	sys.exit(-1)

if options.color:
	if options.color not in colors.keys():
		print 'Invalid color, must be one of ' + str(colors.keys()) + ', see also http://i.imgur.com/hlzHw.png'
		sys.exit(-1)

datadir = os.path.dirname(sys.argv[0])

p = TcxParser()

course = p.parse(args[0])
course.color = options.color
writeCourse(datadir, course)
writeIndex(datadir)

mkdirp('styles')
mkdirp('scripts')
mkdirp('images')
shutil.copy(os.path.join(datadir, 'static', 'styles', 'index.css'), 'styles')
shutil.copy(os.path.join(datadir, 'static', 'styles', 'ride.css'), 'styles')
shutil.copy(os.path.join(datadir, 'static', 'scripts', 'map.js'), 'scripts')
shutil.copy(os.path.join(datadir, 'static', 'scripts', 'mootools-1.2.4-core.js'), 'scripts')
shutil.copy(os.path.join(datadir, 'static', 'images', 'crosshair.png'), 'images')
