import math
import gd

# round x to the smallest integer i such that
#  x < i = k * 10^j for k \in {2,5,10} and j \in |N
def humanRoundUp(x):
	digits = math.floor(math.log(x) / math.log(10))
	mag = int(math.pow(10, digits))

	firstDigit = int(x / mag)

	for i in [2,5,10]:
		if firstDigit < i:
			return i * mag


# TODO generalize with getKmScale
def getVScale(lo, hi, pixels):
	diff = hi - lo

	font_height = gd.fontstrsize(1, '0123456789')[1]

	maxlabels = pixels / (font_height)
	inc = humanRoundUp(diff / maxlabels)

	hlo = int(lo - lo % inc)

	scale = []

	y = hlo

	while y <= hi:
		if y >= lo:
			labelpos = pixels * (y - lo) / diff
			scale.append((str(y), int(round(labelpos + font_height / 2)), int(round(labelpos)) ))
		
		y += inc

	return scale

# TODO generalize with getVScale
def genKmScale(kmf, pixels):

	km = int(kmf)
	# determine maxwidth of labels
	maxw = gd.fontstrsize(1, str(km))[0]

	# this is the hard maximum to ensure no overlap and visually acceptable padding (2 times label width)
	maxlabels = pixels / (maxw * 2)

	# choose a readable label increment
	if maxlabels >= km:
		dist = 1
	else:
		dist = humanRoundUp(kmf / maxlabels)

	scale = []

	for i in range(1, int(kmf / dist) + 1):
		labelpos = pixels * i * dist / kmf
		width = gd.fontstrsize(1, str(i*dist))[0]
		scale.append((str(i*dist), int(round(labelpos - width / 2)), int(round(labelpos))))

	return scale

class PlotConfig:
	class Color:
		label = (0,0,0)
		grid = (128,128,128)
		graph = (255,0,0)
		area = (128,0,0)

	class Dimensions:
		SIZE_PLANE = 1
		SIZE_CANVAS = 2

		width = 400
		height = 250
		type = SIZE_PLANE

		def __init__(self, cfg):
			self.cfg = cfg

		def actualCanvas(self):
			if self.type == self.SIZE_CANVAS:
				return (self.width, self.height)
			else:
				po = self.planeOffset()
				return (self.width + self.cfg.outerPadding + po[0], self.height + self.cfg.outerPadding + po[1])

		def actualPlane(self):
			if self.type == self.SIZE_PLANE:
				return (self.width, self.height)
			else:
				po = self.planeOffset()
				return (self.width - self.cfg.outerPadding - po[0], self.height - self.cfg.outerPadding - po[1])

		def planeOffset(self):
			# x:
			# padding [1/2fh fh 1/2fh] 1/2fw 4fw 1/2fw ticlen 1
			(fw2, fh2) = gd.fontstrsize(self.cfg.font, 'W')
			(fw, fh) = (fw2 / 2 + fw2 % 2, fh2 / 2 + fh2 % 2)

			dx = self.cfg.outerPadding + fw + 4*fw2 + fw + self.cfg.ticLen + 1
			if self.cfg.label.y:
				dx += fh + fh2 + fh

			# y:
			# padding [1/2fh fh 1/2fh] 1/2fh fh 1/2fh ticlen 1
			dy = self.cfg.outerPadding + fh + fh2 + fh + self.cfg.ticLen + 1
			if self.cfg.label.x:
				dy += fh + fh2 + fh

			return (dx,dy)

	class Label:
		x = None
		y = None
		
	label = Label()
	color = Color()
	ticLen = 5
	grid = False
	arrows = False
	renderArea = False
	outerPadding = 10
	font = gd.gdFontSmall

	def __init__(self):
		self.dim = self.Dimensions(self)

class Canvas:
	width = None
	height = None

class Plane:
	x = None
	y = None
	width = None
	height = None

class Geometry:
	canvas = Canvas()
	plane = Plane()

class SimpleDataPlot:
	CANVAS_SIZE = 1
	PLANE_SIZE = 2

	geometry = Geometry()

	def __init__(self):
		self.setSize(self.CANVAS_SIZE, (1000,250))
	
	def setSize(self, plane, size):
		plane_offset = (50,30, -10, -10)
		
		self.geometry.plane.x = plane_offset[0]
		self.geometry.plane.y = plane_offset[1]

		if plane == self.CANVAS_SIZE:
			self.geometry.canvas.width = size[0]
			self.geometry.canvas.height = size[1]
			self.geometry.plane.width = size[0] - plane_offset[0] + plane_offset[2]
			self.geometry.plane.height = size[1] - plane_offset[1] + plane_offset[3]
		else:
			self.geometry.plane.width = size[0]
			self.geometry.plane.height = size[1]
			self.geometry.canvas.width = size[0] + plane_offset[0] - plane_offset[2]
			self.geometry.canvas.height = size[1] + plane_offset[1] - plane_offset[3]

	def t(self, img, p):
		return (p[0], img.size()[1] - 1 - p[1])

	def plotPoints(self, datapoints, filename):
		if len(datapoints) < 2:
			raise ValueError('Need at least two data points')

		x_min = x_max = datapoints[0][0]
		y_min = y_max = datapoints[0][1]

		# determine data bounds
		for p in datapoints:
			x_min = min(x_min, p[0])
			x_max = max(x_max, p[0])
			y_min = min(y_min, p[1])
			y_max = max(y_max, p[1])

#		x_min = int(round(x_min))
#		x_max = int(round(x_max))
#		y_min = int(round(y_min))
#		y_max = int(round(y_max))

		img = gd.image((self.geometry.canvas.width, self.geometry.canvas.height))
		img.colorAllocate((255,255,255))
		label_col = img.colorAllocate((0,0,0))

		# plane
		img.line(self.t(img, (self.geometry.plane.x - 1, self.geometry.plane.y - 1)), self.t(img, (self.geometry.plane.x - 1 + self.geometry.plane.width, self.geometry.plane.y - 1)), label_col)
		img.line(self.t(img, (self.geometry.plane.x - 1, self.geometry.plane.y - 1)), self.t(img, (self.geometry.plane.x - 1, self.geometry.plane.y - 1 + self.geometry.plane.height)), label_col)


		# labels: hscale
		labels = genKmScale(x_max, self.geometry.plane.width)
		yoff = -(gd.fontstrsize(1, '1')[1] / 2 + 3)
		for label in labels:
			img.string(1, self.t(img, (self.geometry.plane.x + label[1], self.geometry.plane.y + yoff)), label[0], label_col)
			src = self.t(img, (self.geometry.plane.x + label[2], self.geometry.plane.y - 1))
			dst = self.t(img, (self.geometry.plane.x + label[2], self.geometry.plane.y - 5))
			img.line(src, dst, label_col)

		# labels: vscale
		labels = getVScale(y_min, y_max, self.geometry.plane.height)
		xoff = -(gd.fontstrsize(1, '9999')[0] + 3)
		for label in labels:
			img.string(1, self.t(img, (self.geometry.plane.x + xoff, self.geometry.plane.y + label[1])), label[0], label_col)
			src = self.t(img, (self.geometry.plane.x - 1, self.geometry.plane.y + label[2]))
			dst = self.t(img, (self.geometry.plane.x - 5, self.geometry.plane.y + label[2]))
			img.line(src, dst, label_col)
			


		# graph
		ink = img.colorAllocate((255,0,0))
		for i in range(len(datapoints) - 1):
			dp = datapoints[i]
#			dp = (int(round(dp[0])), int(round(dp[1])))
			pos_x = self.geometry.plane.x + (self.geometry.plane.width - 1) * (dp[0] - x_min) / (x_max - x_min)
			pos_y = self.geometry.plane.y + (self.geometry.plane.height - 1) * (dp[1] - y_min) / (y_max - y_min)
			src = (int(pos_x), int(img.size()[1] - pos_y - 1))

			dp = datapoints[i+1]
#			dp = (int(round(dp[0])), int(round(dp[1])))
			pos_x = self.geometry.plane.x + (self.geometry.plane.width - 1) * (dp[0] - x_min) / (x_max - x_min)
			pos_y = self.geometry.plane.y + (self.geometry.plane.height - 1) * (dp[1] - y_min) / (y_max - y_min)
			dst = (int(pos_x), int(img.size()[1] - pos_y - 1))


			img.line(src,dst,ink)
#			img.setPixel((pos_x, img.size()[1] - pos_y - 1), ink)

		img.writePng(filename)



#cfg = PlotConfig()
#
#cfg.dim.type = cfg.dim.SIZE_PLANE
#cfg.dim.width = 300
#cfg.dim.height = 120
#
#print 'plane', cfg.dim.actualPlane()
#print 'canvas', cfg.dim.actualCanvas()
