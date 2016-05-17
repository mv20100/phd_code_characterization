from PyDAQmx import *
import numpy as np
import ctypes, time
from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg
from collections import deque

class SyncAIAO(object):

    compatibility_mode = 0          # Set this to 1 on some PC (Mouss)
    trigName = "ai/StartTrigger"
    timeout = 10.0
    mean = 64
    sampling_rate = 1e5
    numSamp=2000
    nbSampCroppedFactor=0.5
    vpp=1.
    offset = 0.

    def __init__(self,device="Dev2",outChan="ao1",inChanList=["ai0"],inRange=(-10.,10.),outRange=(-10.,10.)):
        self.device = device
        self.outChan = outChan
        self.inChanList = inChanList
        self.inRange = inRange
        self.outRange = outRange
        self.running = False
        self.initialize()

    def initialize(self):
        self._sampling_rate = self.sampling_rate
        self._numSamp = self.numSamp
        self.nbSampCropped = int(self.nbSampCroppedFactor * self._numSamp)
        self.AImean = np.zeros(self._numSamp*len(self.inChanList),dtype=np.float64)
        self.AIdata = np.zeros((self.mean,self._numSamp*len(self.inChanList)),dtype=np.float64)
        self.ptr = 0
        self.deque = deque([],self.mean)
        self.AOdata = self.offset + np.hstack([np.linspace(-self.vpp/2.,self.vpp/2.,self._numSamp/2,dtype=np.float64,endpoint=False),
            np.linspace(self.vpp/2.,-self.vpp/2.,self._numSamp/2,dtype=np.float64,endpoint=False)])
        self.counter=0
        self.totalAI=0
        self.AItaskHandle = None
        self.AOtaskHandle = None

    def makeInputStr(self):
        return ",".join([self.device+"/"+inChan for inChan in self.inChanList])
    def makeOutputStr(self):
        return self.device+"/"+self.outChan

    def getNthFullChanName(self,index):
        return self.device+"/"+self.inChanList[index]

    def getNthChanAIdata(self,index):
        return self.AOdata[0:self._numSamp-self.nbSampCropped],self.AIdata[self.ptr,index*self._numSamp:(index+1)*self._numSamp-self.nbSampCropped]

    def getNthChanAImean(self,index):
        return self.AOdata[0:self._numSamp-self.nbSampCropped],self.AImean[index*self._numSamp:(index+1)*self._numSamp-self.nbSampCropped]

    def start(self):
        assert not self.running
        self.running = True
        self.initialize()
        def EveryNCallback(taskHandle, everyNsamplesEventType, nSamples, callbackData):
            # global AItaskHandle, totalAI, AIdata, ptr
            readAI = c_int32()
            self.ptr=(self.ptr+1)%self.mean
            self.deque.append(self.ptr)
            DAQmxReadAnalogF64(self.AItaskHandle,self._numSamp,self.timeout,DAQmx_Val_GroupByChannel,self.AIdata[self.ptr],self._numSamp*len(self.inChanList),byref(readAI),None)
            self.AImean=np.mean(self.AIdata[self.deque],axis=0)
            self.totalAI = self.totalAI + readAI.value
            self.counter=self.counter+1
            # print self.totalAI
            return int(0)

        def DoneCallback(taskHandle, status, callbackData):
            self.clearTasks()
            return int(0)

        self.AItaskHandle = TaskHandle()
        self.AOtaskHandle = TaskHandle()
        self.totalAI=0

        DAQmxCreateTask(None,byref(self.AItaskHandle))
        DAQmxCreateAIVoltageChan(self.AItaskHandle,self.makeInputStr(), None, DAQmx_Val_Cfg_Default, self.inRange[0],self.inRange[1], DAQmx_Val_Volts, None)
        DAQmxCfgSampClkTiming(self.AItaskHandle,None, self._sampling_rate, DAQmx_Val_Rising, DAQmx_Val_ContSamps, self._numSamp)
        DAQmxCreateTask(None,byref(self.AOtaskHandle))
        DAQmxCreateAOVoltageChan(self.AOtaskHandle,self.makeOutputStr(),None,self.outRange[0],self.outRange[1],DAQmx_Val_Volts,None)
        DAQmxCfgSampClkTiming(self.AOtaskHandle,None,self._sampling_rate,DAQmx_Val_Rising,DAQmx_Val_ContSamps,self._numSamp)
        DAQmxCfgDigEdgeStartTrig(self.AOtaskHandle,self.trigName,DAQmx_Val_Rising)

        if self.compatibility_mode == 0:
            EveryNCallbackCWRAPPER = CFUNCTYPE(c_int32,c_void_p,c_int32,c_uint32,c_void_p)
        else:
            EveryNCallbackCWRAPPER = CFUNCTYPE(c_int32,c_ulong,c_int32,c_uint32,c_void_p)
        self.everyNCallbackWrapped = EveryNCallbackCWRAPPER(EveryNCallback)
        DAQmxRegisterEveryNSamplesEvent(self.AItaskHandle,DAQmx_Val_Acquired_Into_Buffer,self._numSamp,0,self.everyNCallbackWrapped,None)

        if self.compatibility_mode == 0:
            DoneCallbackCWRAPPER = CFUNCTYPE(c_int32,c_void_p,c_int32,c_void_p)
        else:
            DoneCallbackCWRAPPER = CFUNCTYPE(c_int32,c_ulong,c_int32,c_void_p)
        self.doneCallbackWrapped = DoneCallbackCWRAPPER(DoneCallback)
        DAQmxRegisterDoneEvent(self.AItaskHandle,0,self.doneCallbackWrapped,None)

        DAQmxWriteAnalogF64(self.AOtaskHandle, self._numSamp, 0, self.timeout, DAQmx_Val_GroupByChannel, self.AOdata, None, None)

        DAQmxStartTask(self.AOtaskHandle)
        DAQmxStartTask(self.AItaskHandle)
        print "Starting acquisition"

    def clearTasks(self):
        if self.AItaskHandle:
            DAQmxStopTask(self.AItaskHandle)
            DAQmxClearTask(self.AItaskHandle)
            self.AItaskHandle = None
        if self.AOtaskHandle:
            DAQmxStopTask(self.AOtaskHandle)
            DAQmxClearTask(self.AOtaskHandle)
            self.AOtaskHandle = None

    def stop(self):
        if self.running:
            self.clearTasks()
            self.setZero()
            self.running = False

    def setZero(self):
        print "Setting output to 0 V"
        clearTaskHandle = TaskHandle()
        DAQmxCreateTask("", byref(clearTaskHandle))
        DAQmxCreateAOVoltageChan(clearTaskHandle, self.makeOutputStr(), None, self.outRange[0],self.outRange[1], DAQmx_Val_Volts, None)
        DAQmxWriteAnalogF64(clearTaskHandle,1,1,self.timeout,DAQmx_Val_GroupByChannel,np.array([0.]),None,None)
        DAQmxStartTask(clearTaskHandle)
        DAQmxClearTask(clearTaskHandle)

    def __del__(self):
        self.stop()

if __name__=="__main__":
    
    app = QtGui.QApplication([])
    win = pg.GraphicsWindow()
    win.resize(1000,600)
    win.setWindowTitle('Pyqtgraph : Live NIDAQmx data')
    pg.setConfigOptions(antialias=True)
    outChan="ao2"
    inChanList=["ai20"]
    syncAiAo = SyncAIAO(device = "Dev1", inChanList=inChanList,outChan=outChan)
    p = win.addPlot(title="Live plot")
    p.addLegend()
    colors = ['m','y','c']
    assert len(colors)>=len(inChanList)
    curves = []
    for idx,inChan in enumerate(inChanList):
        curve = p.plot(pen=colors[idx],name=syncAiAo.getNthFullChanName(idx))
        curves.append(curve)
    
    def update():
        for idx,curve in enumerate(curves):
            x, y = syncAiAo.getNthChanAIdata(idx)
            curve.setData(x=x, y=y)
        if syncAiAo.counter == 1:
            p.enableAutoRange('xy', False)  ## stop auto-scaling after the first data set is plotted
    timer = QtCore.QTimer()
    timer.timeout.connect(update)
    timer.start(50)

    syncAiAo.start()

    import sys 
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        ret = QtGui.QApplication.instance().exec_()
        print "Closing"
        syncAiAo.stop()
        sys.exit(ret)
