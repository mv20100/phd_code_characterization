from PyDAQmx import *
import numpy as np


class TriggedTriangle(object):
    """Class to generate a triangle function on an AO and a sync signal on a counter

    General recipe :
    1.  Assign an object to class TriggedTriangle
    2.  Start the task
    3.  Stop the task (you can then start the task again)
    4.  Clear the task (you can not start it anymore)

    Example :
    ramp100Hz = TriggedTriangle(frequency = 100, Vpp = 5)
    ramp100Hz.start()
    ramp100Hz.stop()
    ramp100Hz.clear()

    Parameters :
    frequency = Number of patterns per second
    Vpp = Amplitude peak-peak in Volts
    AO_Adress = Output signal DAQ address
    counter = Trigger signal DAQ address (PFI 12 port for ctr0)
    trig = Internal clock signal to use as a trigger (leave default)
    nb_points = Total number of points in the ramp (not the whole triangle pattern !)
    
    
    """


    def __init__(self, frequency = 100, Vpp = 5, AO_Address = "Dev2/ao0", counter = "Dev2/ctr0", trig = "/Dev2/Ctr0InternalOutput", nb_points = 2000) :

        ## Creating objects with taskhandle Class
        triangleTaskHandle = TaskHandle()
        triggerTaskHandle = TaskHandle()
        clearTaskHandle = TaskHandle()

        ## Self attributes
        self.triangleTaskHandle = triangleTaskHandle
        self.triggerTaskHandle = triggerTaskHandle
        self.clearTaskHandle = clearTaskHandle
        self.AO_Address = AO_Address

        ##  Pattern generation
        data1 = np.linspace(-Vpp/2.,Vpp/2.,nb_points,dtype=np.float64,endpoint=False)
        data2 = np.linspace(Vpp/2.,-Vpp/2.,nb_points,dtype=np.float64,endpoint=False) 
        data = np.hstack([data1,data2])
        data = np.roll(data,nb_points/2)

        try :
            ##  Tasks creation
            DAQmxCreateTask("", byref(triangleTaskHandle))
            DAQmxCreateTask("", byref(triggerTaskHandle))

            ##  Virtual channels creation
            DAQmxCreateCOPulseChanFreq(triggerTaskHandle, counter, None, DAQmx_Val_Hz, DAQmx_Val_Low, 0., frequency, 0.5)
            DAQmxCreateAOVoltageChan(triangleTaskHandle, AO_Address, None, -10., 10., DAQmx_Val_Volts, None)

            ##  Setting timing parameters
            DAQmxCfgImplicitTiming(triggerTaskHandle, DAQmx_Val_ContSamps, 29)
            DAQmxCfgSampClkTiming(triangleTaskHandle, "", frequency*np.size(data), DAQmx_Val_Rising, DAQmx_Val_ContSamps, 19)

            ##  Write pattern on AO channel
            DAQmxWriteAnalogF64(triangleTaskHandle, 2*nb_points, 0, 10.0, DAQmx_Val_GroupByScanNumber, data, None, None)

            ##  Trigger configuration
            DAQmxCfgDigEdgeStartTrig(triangleTaskHandle, "/Dev2/PFI12", DAQmx_Val_Rising)

        except DAQError as err :
            print("DAQmx Error : %s"%err)

    def start(self) :   
        try :
            ##  Start tasks
            DAQmxStartTask(self.triggerTaskHandle)
            DAQmxStartTask(self.triangleTaskHandle)

        except DAQError as err :
            print("DAQmx Error : %s"%err)

    def stop(self) :
        ##  Stop tasks
        DAQmxStopTask(self.triangleTaskHandle)
        DAQmxStopTask(self.triggerTaskHandle)

    def clear(self) :
        ##  Setting output signal to zero
        DAQmxClearTask(self.triangleTaskHandle)
        DAQmxCreateTask("", byref(self.clearTaskHandle))
        DAQmxCreateAOVoltageChan(self.clearTaskHandle, self.AO_Address, None, -10., 10., DAQmx_Val_Volts, None)
        DAQmxWriteAnalogF64(self.clearTaskHandle,1,1,10,DAQmx_Val_GroupByChannel,np.array([0.]),None,None)
        DAQmxStartTask(self.clearTaskHandle)

        ##  Clear all tasks
        DAQmxClearTask(self.triggerTaskHandle)
        DAQmxClearTask(self.clearTaskHandle)
