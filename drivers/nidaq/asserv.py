from PyDAQmx import *
import numpy as np
import ctypes, time, Queue
from utils.misc import Buffer

class Asserv(object):

    compatibility_mode = 0          # Set this to 1 on some PC (Mouss)
    trigName = "ai/StartTrigger"
    timeout = 10.0
    initial_dds_frequency = 7358910
    get_init_freq_from_dds = True   # Set to False to use initial_dds_frequency as first frequency
    lock = True
    gain = 40000
    cycle_number = 20
    default_freq_mod = 192
    n_samp_per_cycle = 5200
    sampling_rate = 1e6
    discarded_samples_factor = 0.1
    amplitude = 0.5
    inRange = (-1.,1.)
    outRange = (-0.5,0.5)
    running = False
    header = ["Time","DAQ time (s)","Frequency (Hz)","Correction (Hz)","Error","Mean signal (V)"]

    def __init__(self, device="Dev1",outChan="ao3",inChan="ai0",dds_device=None):
    
        self.device = device
        self.outChan = outChan
        self.inChan = inChan
        self.dds = dds_device

        self.dataQueue = None

        self.freq_mod = self.default_freq_mod

    def initialize(self):
        
        self.AIdata = np.zeros(self.n_samp_per_cycle,dtype=np.float64)
        self.mean_buffer = Buffer(20)
        self.AOdata = np.hstack([-self.amplitude *np.ones(self.n_samp_per_cycle/2),
                                    self.amplitude *np.ones(self.n_samp_per_cycle/2)])
        self.AItaskHandle = None
        self.AOtaskHandle = None
        self.ptr = 0
        self.ctr = 0

        if self.get_init_freq_from_dds:         # Overide initial frequency
            self.initial_dds_frequency = self.dds.frequency
        self.dds_frequency = self.initial_dds_frequency
        self.bufferLength = 2*self.cycle_number*self.n_samp_per_cycle*int(1e8/(2*self.cycle_number*self.n_samp_per_cycle))
        self.errorTab = np.zeros(self.cycle_number,dtype=np.float64)
        self.powerTab = np.zeros(self.cycle_number,dtype=np.float64)
        self.nbSampCropped = int(self.n_samp_per_cycle/2*self.discarded_samples_factor)

    @property 
    def update_interval(self):
        return self.cycle_number/float(self.freq_mod)

    @property
    def freq_mod(self):
        return self.sampling_rate/float(self.n_samp_per_cycle)

    @freq_mod.setter
    def freq_mod(self,freq_mod):
        self.n_samp_per_cycle = 2*int(self.sampling_rate/(2*freq_mod))

    def start(self):

        assert not self.running
        self.running = True
        self.initialize()

        print ("Modulation frequency: {}".format(self.freq_mod)) 
        print("DDS Update Intervall: {}".format(self.update_interval))
        print("Number of samples per cycle: {}".format(self.n_samp_per_cycle))

        def EveryNCallback(taskHandle, everyNsamplesEventType, nSamples, callbackData):
            readAI = c_int32()
            DAQmxReadAnalogF64(self.AItaskHandle,self.n_samp_per_cycle,self.timeout,DAQmx_Val_GroupByChannel,self.AIdata,self.n_samp_per_cycle,byref(readAI),None)
            self.ptr = (self.ptr + 1) % self.cycle_number
            self.AIdata = np.roll(self.AIdata, -1)
            mean_over_resonance = np.mean(self.AIdata[self.nbSampCropped:self.n_samp_per_cycle/2])
            mean_below_resonance = np.mean(self.AIdata[self.n_samp_per_cycle/2+self.nbSampCropped:self.n_samp_per_cycle])
            error = mean_below_resonance - mean_over_resonance
            self.errorTab[self.ptr] = error
            self.powerTab[self.ptr] = (mean_over_resonance + mean_below_resonance)/2
            if self.ptr == 0:
                self.ctr += 1
                daqTime = self.ctr * self.cycle_number*self.n_samp_per_cycle/float(self.sampling_rate)
                meanError = np.mean(self.errorTab)
                correction = self.gain*meanError
                if self.lock:
                    self.dds_frequency += correction 
                    self.dds.frequency = self.dds_frequency
                mean_power = np.mean(self.powerTab)
                self.mean_buffer.append(mean_power)
                if self.dataQueue:
                    self.dataQueue.put([time.time(),daqTime,self.dds_frequency,self.dds_frequency-self.initial_dds_frequency,meanError,mean_power])                
            return int(0)       

        def DoneCallback(taskHandle, status, callbackData):
            self.clearTasks()
            return int(0)

        self.AItaskHandle = TaskHandle()
        self.AOtaskHandle = TaskHandle()

        DAQmxCreateTask(None,byref(self.AItaskHandle))
        DAQmxCreateAIVoltageChan(self.AItaskHandle,self.device + '/' + self.inChan, None, DAQmx_Val_Cfg_Default, self.inRange[0],self.inRange[1], DAQmx_Val_Volts, None)
        DAQmxCfgSampClkTiming(self.AItaskHandle,None, self.sampling_rate, DAQmx_Val_Rising, DAQmx_Val_ContSamps, self.n_samp_per_cycle)
        DAQmxCreateTask(None,byref(self.AOtaskHandle))
        DAQmxCreateAOVoltageChan(self.AOtaskHandle,self.device + '/' + self.outChan,None,self.outRange[0],self.outRange[1],DAQmx_Val_Volts,None)
        DAQmxCfgSampClkTiming(self.AOtaskHandle,None,self.sampling_rate,DAQmx_Val_Rising,DAQmx_Val_ContSamps,self.n_samp_per_cycle)
        DAQmxCfgDigEdgeStartTrig(self.AOtaskHandle,self.trigName,DAQmx_Val_Rising)

        DAQmxCfgInputBuffer(self.AItaskHandle, c_uint32(self.bufferLength))

        if self.compatibility_mode == 0:
            EveryNCallbackCWRAPPER = ctypes.CFUNCTYPE(ctypes.c_int32,ctypes.c_void_p,ctypes.c_int32,ctypes.c_uint32,ctypes.c_void_p)
        else:
            EveryNCallbackCWRAPPER = ctypes.CFUNCTYPE(ctypes.c_int32,ctypes.c_ulong,ctypes.c_int32,ctypes.c_uint32,ctypes.c_void_p)
        self.everyNCallbackWrapped = EveryNCallbackCWRAPPER(EveryNCallback)
        DAQmxRegisterEveryNSamplesEvent(self.AItaskHandle,DAQmx_Val_Acquired_Into_Buffer,self.n_samp_per_cycle,0,self.everyNCallbackWrapped,None)
       
        if self.compatibility_mode == 0:
            DoneCallbackCWRAPPER = ctypes.CFUNCTYPE(ctypes.c_int32,ctypes.c_void_p,ctypes.c_int32,ctypes.c_void_p)
        else:
            DoneCallbackCWRAPPER = ctypes.CFUNCTYPE(ctypes.c_int32,ctypes.c_ulong,ctypes.c_int32,ctypes.c_void_p)
        self.doneCallbackWrapped = DoneCallbackCWRAPPER(DoneCallback)
        DAQmxRegisterDoneEvent(self.AItaskHandle,0,self.doneCallbackWrapped,None)

        DAQmxWriteAnalogF64(self.AOtaskHandle, self.n_samp_per_cycle, 0, self.timeout, DAQmx_Val_GroupByChannel, self.AOdata, None, None)

        DAQmxStartTask(self.AOtaskHandle)
        DAQmxStartTask(self.AItaskHandle)
        print "Starting asserv"

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
        DAQmxCreateAOVoltageChan(clearTaskHandle, self.device + '/' + self.outChan, None, self.outRange[0],self.outRange[1], DAQmx_Val_Volts, None)
        DAQmxWriteAnalogF64(clearTaskHandle,1,1,self.timeout,DAQmx_Val_GroupByChannel,np.array([0.]),None,None)
        DAQmxStartTask(clearTaskHandle)
        DAQmxClearTask(clearTaskHandle)

    def __del__(self):
        self.stop()