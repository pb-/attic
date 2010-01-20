import math
import random
import dataplot


# generate test data
w = 400
data = []

for x in range(w):
	y = 100
	for f in range(1,11):
		random.seed(f)
		y += math.sin(float(x)/w * 2*math.pi * f + random.random() * 2*math.pi) * 20 / f
	data.append((x,y))

# plot it
p = dataplot.Plotter()
cfg = dataplot.PlotConfig()
img = p.plotPoints(data, cfg)
img.writePng('plot.png')

# plot if differently!
cfg.color.background = (250,250,250)
cfg.color.graph = (0,0,255)
cfg.color.area = (230,230,255)
cfg.renderArea = True
cfg.label.x = 'x'
cfg.label.y = 'funky(x)'
cfg.ticLen = 2
cfg.dim.width = 650
cfg.dim.height = 130
img = p.plotPoints(data, cfg)
img.writePng('plot2.png')
