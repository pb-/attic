#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License along
#    with this program; if not, write to the Free Software Foundation, Inc.,
#    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#

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

def genXScale(cfg, lo, hi, scalePixelLen):
	maxLabelWidth = gd.fontstrsize(cfg.font, '%d' % hi)[0]
	return map(lambda x: (str(x[0]),x[1]), genScale(lo, hi, scalePixelLen, scalePixelLen / (maxLabelWidth * 2)))

def genYScale(cfg, lo, hi, scalePixelLen):
	fontHeight = cfg.dim.refChar[1]
	return map(lambda x: ('%4d' % x[0],x[1]), genScale(lo, hi, scalePixelLen, scalePixelLen / fontHeight))

def genScale(lo, hi, scalePixelLen, maxLabels):
	diff = hi - lo
	inc = humanRoundUp(max(diff / maxLabels, 1))
	hlo = int(lo - lo % inc)
	x = hlo
	
	scale = []

	while x <= hi:
		if x >= lo:
			pixelPos = scalePixelLen * (x - lo) / diff
			scale.append((x, int(round(pixelPos))))
		x += inc

	return scale

class PlotConfig:
	class Color:
		background = (255,255,255)
		label = (0,0,0)
		grid = (192,192,192)
		graph = (255,0,0)
		area = (255,230,230)

	class Dimensions:
		SIZE_PLANE = 1
		SIZE_CANVAS = 2

		width = 400
		height = 250
		type = SIZE_PLANE

		def __init__(self, cfg):
			self.cfg = cfg
			self.refChar = gd.fontstrsize(self.cfg.font, 'W')

		def padPos(self):
			return 0

		def padLen(self):
			return self.cfg.outerPadding

		def xLabelPos(self):
			return self.padPos() + self.padLen()

		def xLabelLen(self):
			if self.cfg.label.x:
				return self.refChar[1]
			else:
				return 0

		def xLabelBaselinePos(self):
			return self.xLabelPos() + int(self.refChar[1])

		def xScalePos(self):
			return self.xLabelPos() + self.xLabelLen()

		def xScaleLen(self):
			return int(self.refChar[1])

		def xScaleBaselinePos(self):
			return self.xScalePos() + int(self.refChar[1])

		def xTicPos(self):
			return self.xScalePos() + self.xScaleLen()

		def xTicLen(self):
			return self.cfg.ticLen

		def xPlaneBorderPos(self):
			return self.xTicPos() + self.xTicLen()

		def xPlaneBorderLen(self):
			return 1

		def yLabelPos(self):
			return self.padPos() + self.padLen()

		def yLabelLen(self):
			if self.cfg.label.y:
				return self.refChar[1]
			else:
				return 0

		def yLabelBaselinePos(self):
			return self.yLabelPos()

		def yScalePos(self):
			return self.yLabelPos() + self.yLabelLen()

		def yScaleLen(self):
			return 5 * self.refChar[0]

		def yScaleBaselinePos(self):
			return self.yScalePos() + self.refChar[0] / 2

		def yTicPos(self):
			return self.yScalePos() + self.yScaleLen()

		def yTicLen(self):
			return self.cfg.ticLen

		def yPlaneBorderPos(self):
			return self.yTicPos() + self.yTicLen()

		def yPlaneBorderLen(self):
			return 1

		def planePos(self):
			return (self.yPlaneBorderPos() + self.yPlaneBorderLen(), self.xPlaneBorderPos() + self.xPlaneBorderLen())

		def planeSize(self):
			if self.type == self.SIZE_PLANE:
				return (self.width, self.height)

		def canvasSize(self):
			if self.type == self.SIZE_PLANE:
				pp = self.planePos()
				ps = self.planeSize()

				return (pp[0] + ps[0] + self.cfg.outerPadding, pp[1] + ps[1] + self.cfg.outerPadding)
			

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


class Plotter:
	def plotPoints(self, datapoints, cfg):
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

		img = gd.image(cfg.dim.canvasSize())
		img.origin((0,img.size()[1] - 1), 1, -1)

		img.colorAllocate(cfg.color.background)
		labelCol = img.colorAllocate(cfg.color.label)
		gridCol = img.colorAllocate(cfg.color.grid)

		img.setStyle((gridCol, gridCol, gridCol, gd.gdTransparent, gd.gdTransparent))
		
		planePos = cfg.dim.planePos()
		planeSize = cfg.dim.planeSize()

		# plane frame
		img.line((cfg.dim.yPlaneBorderPos(), cfg.dim.xPlaneBorderPos()), (cfg.dim.yPlaneBorderPos() + planeSize[0], cfg.dim.xPlaneBorderPos()), labelCol)
		img.line((cfg.dim.yPlaneBorderPos(), cfg.dim.xPlaneBorderPos()), (cfg.dim.yPlaneBorderPos(), cfg.dim.xPlaneBorderPos() + planeSize[1]), labelCol)

		img.line((cfg.dim.yPlaneBorderPos(), planePos[1] + planeSize[1]),(cfg.dim.yPlaneBorderPos() + planeSize[0] + 1, planePos[1] + planeSize[1]), gridCol)
		img.line((planePos[0] + planeSize[0],cfg.dim.xPlaneBorderPos()),(planePos[0] + planeSize[0],cfg.dim.xPlaneBorderPos() + planeSize[1] + 1), gridCol)

		# labels
		if cfg.label.x:
			mx = planePos[0] + planeSize[0] / 2
			mxl = mx - gd.fontstrsize(cfg.font, cfg.label.x)[0] / 2
			img.string(cfg.font, (mxl, cfg.dim.xLabelBaselinePos()), cfg.label.x, labelCol)

		if cfg.label.y:
			my = planePos[1] + planeSize[1] / 2
			myb = my - gd.fontstrsize(cfg.font, cfg.label.y)[0] / 2
			img.stringUp(cfg.font, (cfg.dim.yLabelBaselinePos(), myb), cfg.label.y, labelCol)

		# area
		if cfg.renderArea:
			datapoints.insert(0, (x_min,y_min))
			datapoints.append((x_max,y_min))

			poly = map(lambda p: (
				int(planePos[0] + (planeSize[0] - 1) * (p[0] - x_min) / (x_max - x_min)),
				int(planePos[1] + (planeSize[1] - 1) * (p[1] - y_min) / (y_max - y_min))
			), datapoints)

			datapoints.pop(0)
			datapoints.pop()

			areaCol = img.colorAllocate(cfg.color.area)
			img.filledPolygon(poly, areaCol)
		
		# hscale & grid
		labels = genXScale(cfg, x_min, x_max, planeSize[0])
		for label in labels:
			img.string(cfg.font, (planePos[0] + label[1] - gd.fontstrsize(cfg.font, label[0])[0] / 2, cfg.dim.xScaleBaselinePos()), label[0], labelCol)
			src = (planePos[0] + label[1], cfg.dim.xTicPos())
			dst = (planePos[0] + label[1], cfg.dim.xTicPos() + cfg.dim.xTicLen() - 1)
			img.line(src, dst, labelCol)

			if cfg.grid:
				src = (planePos[0] + label[1], planePos[1])
				dst = (planePos[0] + label[1], planePos[1] + planeSize[1] - 1)
				img.line(src, dst, gd.gdStyled)

		# vscale & grid
		labels = genYScale(cfg, y_min, y_max, planeSize[1])
		for label in labels:
			img.string(cfg.font, (cfg.dim.yScaleBaselinePos(), planePos[1] + label[1] + cfg.dim.refChar[1] / 2), label[0], labelCol)
			src = (cfg.dim.yTicPos(), planePos[1] + label[1])
			dst = (cfg.dim.yTicPos() + cfg.dim.yTicLen() - 1, planePos[1] + label[1])
			img.line(src, dst, labelCol)
			
			if cfg.grid:
				src = (planePos[0], planePos[1] + label[1])
				dst = (planePos[0] + planeSize[0] - 1, planePos[1] + label[1])
				img.line(src, dst, gd.gdStyled)


		# graph
		ink = img.colorAllocate(cfg.color.graph)
		for i in range(len(datapoints) - 1):
			dp = datapoints[i]
			posX = planePos[0] + (planeSize[0] - 1) * (dp[0] - x_min) / (x_max - x_min)
			posY = planePos[1] + (planeSize[1] - 1) * (dp[1] - y_min) / (y_max - y_min)
			src = (int(posX), int(posY))

			dp = datapoints[i+1]
			posX = planePos[0] + (planeSize[0] - 1) * (dp[0] - x_min) / (x_max - x_min)
			posY = planePos[1] + (planeSize[1] - 1) * (dp[1] - y_min) / (y_max - y_min)
			dst = (int(posX), int(posY))

			img.line(src, dst, ink)

		return img

