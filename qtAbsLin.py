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
        self.fitcurve_test=p.plot(pen="r",name="Fit test")
        self.initcurve1=p.plot(pen=pen,name="Init 1")
        self.fitcurve_ref=p.plot(pen="r",name="Fit ref")
        self.initcurve2=p.plot(pen=pen,name="Init 2")
        self.p=p
        # self.label = self.p.addItem(pg.LabelItem("test"))
    def fit(self):
    	x,y_test = self.syncAiAo.getNthChanAIdata(0)
    	x,y_ref = self.syncAiAo.getNthChanAIdata(1)
        print("Fitting data")
    	init1, fitOutTest = fitTwoGaussians(copy.copy(x),copy.copy(y_test))
    	init2, fitOutRef = fitTwoGaussians(copy.copy(x),copy.copy(y_ref))
    	self.fitcurve_test.setData(x=x,y=fitOutTest.best_fit)
    	self.initcurve1.setData(x=x,y=init1)
     	self.fitcurve_ref.setData(x=x,y=fitOutRef.best_fit)
    	self.initcurve2.setData(x=x,y=init2)
    	print computeShift(fitOutRef,fitOutTest)    	
    	self.setCurvesVisible(True)
    def hideCurves(self):
    	self.setCurvesVisible(False)
    def showCurves(self):
    	self.setCurvesVisible(True)
    def setCurvesVisible(self,visibleBool):
    	curves = [self.fitcurve_test,self.fitcurve_ref,self.initcurve1,self.initcurve2]
    	for curve in curves:
    		curve.setVisible(visibleBool)

if __name__=="__main__":
    
    app = QtGui.QApplication([])
    win = pg.GraphicsWindow()
    win.resize(1000,600)
    win.setWindowTitle('Pyqtgraph : Live NIDAQmx data')
    
    pg.setConfigOptions(antialias=True)
    outChan="ao0"
    inChanList=["ai0","ai2"]
    syncAiAo = SyncAIAO(inChanList=inChanList,outChan=outChan,inRange=(-10.,10.),outRange=(-10.,10.))
    syncAiAo.vpp=8
    syncAiAo.numSamp=4000
    syncAiAo.nbSampCropped=2000 
    # syncAiAo = SyncAIAO(inChanList=inChanList,outChan=outChan,vpp=0.8,numSamp=4000,nbSampCropped=2000,inRange=(-10.,10.),outRange=(-1.,1.))
    p = win.addPlot(title="Live plot")
    p.addLegend()

    colors = ['m','c']
    assert len(colors)>=len(inChanList)
    curves = []
    for idx,inChan in enumerate(inChanList):
        curve = p.plot(pen=colors[idx],name=syncAiAo.getNthFullChanName(idx))
        curves.append(curve)
    
    def update():
        for idx,curve in enumerate(curves):
            x, y = syncAiAo.getNthChanAIdata(idx)
            curve.setData(x=x,y=y)
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