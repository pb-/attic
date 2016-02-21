import math
import sys
import gd
import xml.sax
import xml.sax.handler

class GpxIcon(xml.sax.handler.ContentHandler):
	def __init__(self):
		self.latMin = None
		self.lonMin = None
		self.latMax = None
		self.lonMax = None
		self.points = []

	def parse(self, file):
		xml.sax.parse(file, self)
	
	def startElement(self, element, attrs):
		if element == 'trkpt':
			lat = math.pi * float(attrs.getValue('lat')) / 180
			lon = math.pi * float(attrs.getValue('lon')) / 180

			if self.latMin == None:
				self.latMin = lat
				self.latMax = lat
				self.lonMin = lon
				self.lonMin = lon
			else:
				self.latMin = min(self.latMin, lat)
				self.latMax = max(self.latMax, lat)
				self.lonMin = min(self.lonMin, lon)
				self.lonMax = max(self.lonMax, lon)

			self.points.append((lat,lon))
	

	def projectMercator(self):
		
		projPoints = []
		first = True

		# project
		for p in self.points:
			pp = (p[1], math.log(math.tan(math.pi / 4 + p[0] / 2)))
			projPoints.append(pp)

			if first:
				xMin = xMax = pp[0]
				yMin = yMax = pp[1]
				first = False
			else:
				xMin = min(xMin, pp[0])
				xMax = max(xMax, pp[0])
				yMin = min(yMin, pp[1])
				yMax = max(yMax, pp[1])

		# normalize
		dx = xMax - xMin
		dy = yMax - yMin

		if dx > dy:
			self.sy = dy / dx
			self.sx = 1
		else:
			self.sy = 1
			self.sx = dx / dy

		self.projPoints = map(lambda pp: ((pp[0] - xMin) / dx, (pp[1] - yMin) / dy), projPoints)



	def render(self, s):
		self.projectMercator()

		img = gd.image((s,s))
		img.origin((0,s-1),1,-1)
		bg = img.colorAllocate((255,255,255))
		img.colorTransparent(bg)

		ink = img.colorAllocate((0,0,0))

		xMax = s - 1
		yMax = s - 1

		tx = (xMax - self.sx * xMax) / 2
		ty = (yMax - self.sy * yMax) / 2

		points = map(lambda p: (int(tx + self.sx * round(p[0] * xMax)), int(round(ty + self.sy * p[1] * yMax))), self.projPoints)

		img.lines(points, ink)


		return img
		


#g = GpxHandler()
#g.parse(sys.argv[1])
#g.projectMercator()
#g.render(128).writePng('icon.png')


