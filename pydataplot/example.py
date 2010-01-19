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
img = p.plotPoints(data, dataplot.PlotConfig())
img.writePng('plot.png')
