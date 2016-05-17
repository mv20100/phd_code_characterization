from drivers.nidaq.syncAIAO import *
from pyqtgraph.Qt import QtGui, QtCore
import numpy as np
import pyqtgraph as pg
from utils.fitting import *
from utils.calculs import computeShift
import copy

class FitWindow(QtGui.QDialog):    # any super class is okay
    def __init__(self,syncAiAo,p,parent=None):
        super(FitWindow, self).__init__(parent)
        self.fitButton = QtGui.QPushButton('Fit')
        self.hideButton = QtGui.QPushButton('Hide')
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.fitButton)
        layout.addWidget(self.hideButton)
        self.setLayout(layout)
        self.fitButton.clicked.connect(self.fit)
        self.hideButton.clicked.connect(self.hideCurves)
        self.syncAiAo=syncAiAo
        pen=pg.mkPen((0, 255, 0,30))
        self.fitcurve=p.plot(pen="r",name="Fit")
        self.initcurve=p.plot(pen=pen,name="Init")
        self.p=p
        # self.label = self.p.addItem(pg.LabelItem("test"))
    def fit(self):
    	x,y = self.syncAiAo.getNthChanAIdata(0)
    	init, fitOut = fitLorentzian(copy.copy(x),copy.copy(y))
    	self.fitcurve.setData(x=x,y=fitOut.best_fit)
    	self.initcurve.setData(x=x,y=init)  	
    	self.setCurvesVisible(True)
    def hideCurves(self):
    	self.setCurvesVisible(False)
    def showCurves(self):
    	self.setCurvesVisible(True)
    def setCurvesVisible(self,visibleBool):
    	curves = [self.fitcurve,self.initcurve]
    	for curve in curves:
    		curve.setVisible(visibleBool)

if __name__=="__main__":
    
    app = QtGui.QApplication([])
    win = pg.GraphicsWindow()
    win.resize(1000,600)
    win.setWindowTitle('Pyqtgraph : Live NIDAQmx data')
    
    pg.setConfigOptions(antialias=True)
    outChan="ao2"
    inChanList=["ai0"]
    syncAiAo = SyncAIAO(inChanList=inChanList,outChan=outChan,inRange=(-1.,1.),outRange=(-1.,1.))
    p = win.addPlot(title="Live plot")
    p.addLegend()

    colors = [pg.mkPen((0, 255, 0,100)),pg.mkPen((0, 255, 0,100))]
    assert len(colors)>=len(inChanList)
    curves = []
    meanCurves = []
    for idx,inChan in enumerate(inChanList):
        curve = p.plot(pen=colors[idx],name=syncAiAo.getNthFullChanName(idx))
        curves.append(curve)
        meanCurve = p.plot(pen="y",name=syncAiAo.getNthFullChanName(idx)+" mean")
        meanCurves.append(meanCurve)
    
    def update():
        for idx,curve in enumerate(curves):
            x, y = syncAiAo.getNthChanAIdata(idx)
            x2, y2 = syncAiAo.getNthChanAImean(idx)
            curve.setData(x=x,y=y)
            meanCurves[idx].setData(x=x2,y=y2)
        if syncAiAo.counter == 1:
            p.enableAutoRange('xy', False)  ## stop auto-scaling after the first data set is plotted
    timer = QtCore.QTimer()
    timer.timeout.connect(update)
    timer.start(50)

    window = FitWindow(syncAiAo,p)
    window.show()
    syncAiAo.start()

    import sys 
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        ret = QtGui.QApplication.instance().exec_()
        print "Closing"
        syncAiAo.stop()
        sys.exit(ret)