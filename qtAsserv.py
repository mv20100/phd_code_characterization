from drivers import *
print "Driver loaded"
from drivers.nidaq.asserv import Asserv
from PyDAQmx import *
import numpy as np
from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg
import sys


default_fm_dev = 400			# Profondeur de modulation (Hz pour 5 V)



fs = E8254A(gpibAdress=19,name="freqSynth")

default_frequency = fs.frequency

sampling_rate = 1e6 # Hz
modulation_frequency = 271 # Hz
cycle_number = 50 # Number of cycles between fc correction

n_samples_per_cycle = int(sampling_rate/(modulation_frequency*2))*2 #Make sure that this is divisible by 2
modulation_frequency = sampling_rate/n_samples_per_cycle
discarded_samples = n_samples_per_cycle/4
gain = 100000
amplitude = 1 # V
waveform = np.hstack([-amplitude *np.ones(n_samples_per_cycle/2),
	amplitude *np.ones(n_samples_per_cycle/2)])
# dds_frequency = default_frequency

asserv = Asserv(dds_frequency=default_frequency, gain = gain, device="Dev2",outChan="ao2",inChanList=["ai0"],numSamp=n_samples_per_cycle,nbSampCropped=discarded_samples,vpp=2*amplitude,freq=sampling_rate,inRange=(-5.,5.),outRange=(-10.,10.), waveform =waveform, cycle_number=cycle_number)

app = QtGui.QApplication([])
win = pg.GraphicsWindow()
win.resize(1000,600)
win.setWindowTitle('Pyqtgraph : Live NIDAQmx data')
pg.setConfigOptions(antialias=True)
p1 = win.addPlot(title="correction_DDS", col = 0, row = 0)
p1.addLegend()

p2 = win.addPlot(title="error signal", col = 0, row = 1)
p2.addLegend()

p3 = win.addPlot(title="laser power", col = 0, row = 2)
p3.addLegend()

p4 = win.addPlot(title="aux photodiode", col = 0, row = 3)
p4.addLegend()

p5 = win.addPlot(title="therminstance", col = 0, row = 4)
p5.addLegend()

curve = p1.plot(pen = 'm', name = 'DDS_freq')
curve2 = p2.plot(pen = 'c', name = 'error_signal')
curve3 = p3.plot(pen = 'r', name = 'transmitted_power')
curve4 = p4.plot(pen = 'g', name = 'aux photodiode')
curve5 = p5.plot(pen = 'y', name = 'thermistance')
def update() :
    x, y1, y2, y3, y4, y5 = asserv.graph[0], asserv.graph[1], asserv.graph[2], asserv.graph[3], asserv.graph[4], asserv.graph[5]
    curve.setData(x=x, y=y1)
    curve2.setData(x=x, y=y2)
    curve3.setData(x=x, y=y3)
    curve4.setData(x=x, y=y4)
    curve5.setData(x=x, y=y5)
timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(50)
asserv.start()

if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
    ret = QtGui.QApplication.instance().exec_()
    print "Closing"
    asserv.stop()
    sys.exit(ret)
