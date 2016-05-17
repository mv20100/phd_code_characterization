from PyDAQmx import *
import numpy as np
import matplotlib.pyplot as plt
import time
from savitzky_golay import savitzky_golay
import warnings

class NIUSB6259(object):

	def __init__(self,devID='Dev2'):
		self.devID = devID
		self.center = 0

	def read_voltage_on_output(self,channel, samples = 10):
		return self.getInputVoltage('_'+channel+'_vs_aognd',samples=samples) 

	def getInputVoltage(self,channel="ai0",range=(-10,10),samples=1000):
		source = self.devID+"/"+channel
		# Declaration of variable passed by reference
		taskHandle = TaskHandle()
		read = int32()
		data = np.zeros((samples,), dtype=np.float64)

		try:
			# DAQmx Configure Code
			DAQmxCreateTask("",byref(taskHandle))
			DAQmxCreateAIVoltageChan(taskHandle,source,"",DAQmx_Val_Cfg_Default,range[0],range[1],DAQmx_Val_Volts,None)
			# DAQmxCfgSampClkTiming(taskHandle,"",10000.0,DAQmx_Val_Rising,DAQmx_Val_FiniteSamps,1000)
			DAQmxCfgSampClkTiming(taskHandle,"",10000.0,DAQmx_Val_Rising,DAQmx_Val_ContSamps,1000)
			# DAQmx Start Code
			DAQmxStartTask(taskHandle)

			# DAQmx Read Code
			DAQmxReadAnalogF64(taskHandle,samples,10.0,DAQmx_Val_GroupByChannel,data,samples,byref(read),None)

			# print "Acquired %d points"%read.value
		except DAQError as err:
			print "DAQmx Error: %s"%err
		finally:
			if taskHandle:
				# DAQmx Stop Code
				DAQmxStopTask(taskHandle)
				DAQmxClearTask(taskHandle)
		
		return float(np.average(data))

	def setOutputVoltage(self,voltage,channel="ao0",range=(-10,10)):
		source = self.devID+"/"+channel
		taskHandle = TaskHandle()
		data = np.array(voltage, dtype=np.float64)

		try:
			DAQmxCreateTask("",byref(taskHandle))
			DAQmxCreateAOVoltageChan(taskHandle,source,"",range[0],range[1],DAQmx_Val_Volts,None)
			DAQmxStartTask(taskHandle)
			DAQmxWriteAnalogF64(taskHandle,1,0,-1,DAQmx_Val_GroupByChannel,data,None,None)

		except DAQError as err:
			print "DAQmx Error: %s"%err
		finally:
			if taskHandle:
				DAQmxStopTask(taskHandle)
				DAQmxClearTask(taskHandle)
		
		return
		
	def syncReadWrite(self,inData,readChan="ai0",writeChan="ao0",inRange=(-10,10),outRange=(-10,10),rate=1000,presetVoltage=True):
		#Set the voltage to the first value to avoid 1st data point error
		if presetVoltage:
			self.setOutputVoltage(inData[0],writeChan,outRange)
		
		samples = len(inData)
		readChanID = self.devID+"/"+readChan
		writeChanID = self.devID+"/"+writeChan
		writeTaskHandle = TaskHandle()
		readTaskHandle = TaskHandle()
		read = int32()
		
		outData = np.zeros((samples,), dtype=np.float64)
		
		try:
			DAQmxCreateTask("",byref(writeTaskHandle))
			DAQmxCreateAOVoltageChan(writeTaskHandle,writeChanID,"",outRange[0],outRange[1],DAQmx_Val_Volts,None)
			DAQmxCfgSampClkTiming(writeTaskHandle,"",rate,DAQmx_Val_Rising,DAQmx_Val_FiniteSamps,samples)
			
			DAQmxCreateTask("",byref(readTaskHandle))
			DAQmxCreateAIVoltageChan(readTaskHandle,readChanID,"",DAQmx_Val_Cfg_Default,inRange[0],inRange[1],DAQmx_Val_Volts,None)
			DAQmxCfgSampClkTiming(readTaskHandle,"/"+self.devID+"/ao/SampleClock",rate,DAQmx_Val_Rising,DAQmx_Val_FiniteSamps,samples)

			DAQmxWriteAnalogF64(writeTaskHandle,samples,0,10.0,DAQmx_Val_GroupByChannel,inData,None,None)		
			DAQmxStartTask(readTaskHandle)
			DAQmxStartTask(writeTaskHandle)	
			
			DAQmxReadAnalogF64(readTaskHandle,samples,10.0,DAQmx_Val_GroupByChannel,outData,samples,byref(read),None)
	
			# print "Acquired %d points"%read.value
	
		except DAQError as err:
			print "DAQmx Error: %s"%err
		finally:
			if readTaskHandle:
				DAQmxStopTask(readTaskHandle)
				DAQmxClearTask(readTaskHandle)	
			if writeTaskHandle:
				DAQmxStopTask(writeTaskHandle)
				DAQmxClearTask(writeTaskHandle)
		# Go back to 0 after measure
		# if presetVoltage: self.setOutputVoltage(0.,writeChan,vrange)
		
		return outData
	
	def syncRamp(self,Vpp=0.5,offset=0,samples=1000,readChan="ai0",writeChan="ao0",rate=1000,fig=None,ax=None,inRange=(-10,10),outRange=(-10,10)):
		inData = np.linspace(-Vpp/2.+offset,Vpp/2.+offset,samples)
		outData = self.syncReadWrite(inData,readChan,writeChan,inRange,outRange,rate)
		if fig != None:
			plt.figure(fig)
			ax = plt.gca()
		if fig or ax:
			ax.plot(inData,outData)
			plt.draw()
			plt.show(block=False)
		return inData,outData

	def getArgMin(self,Vpp=1,offset=0.,samples=1000,readChan="ai0",writeChan="ao0",rate=1000,fig=None,ax=None,filter=51):
		inData, outData = self.syncRamp(Vpp,offset,samples,readChan,writeChan,rate)
		filteredData = savitzky_golay(outData,filter,3)
		minimum = min(filteredData)
		inVoltageAtMin = inData[filteredData.argmin()]
		if fig != None:
			plt.figure(fig)
			ax = plt.gca()
		if fig or ax:
			print "Plotting    ",
			ax.plot(inData,outData,'k')
			ax.plot(inData,filteredData,'g')
			ax.plot(inVoltageAtMin,minimum,'r+')
			plt.draw()
			plt.show(block=False)
			print "[DONE]"
		
		return minimum,inVoltageAtMin

		
	def syncAOandDO(self):		
		warnings.warn("deprecated", DeprecationWarning)
		rate = 10000
	
		coTaskHandle = TaskHandle()
		DAQmxCreateCOPulseChanTime(coTaskHandle,"/Dev2/ctr0","",DAQmx_Val_Rising,DAQmx_Val_Low,1,0.5,1)
		
		doTaskHandle = TaskHandle()
		DAQmxCreateDOChan(doTaskHandle,"/Dev2/port1/line0","",None)
		DAQmxCfgSampClkTiming(doTaskHandle,"",rate,None,DAQmx_Val_ContSamps,None)
		
		
		doChanID = self.devID+"/"+readChan
		
		doTaskHandle = TaskHandle()
		

		writeTaskHandle = TaskHandle()
		readTaskHandle = TaskHandle()
		trigTaskHandle = TaskHandle()
		read = int32()
		
		outData = np.zeros((samples,), dtype=np.float64)
		trigData = np.zeros((samples,), dtype=np.float64)
		trigData[0:1] = 5
		
		try:
			DAQmxCreateTask("",byref(writeTaskHandle))
			DAQmxCreateAOVoltageChan(writeTaskHandle,writeChanID,"",vrange[0],vrange[1],DAQmx_Val_Volts,None)
			DAQmxCfgSampClkTiming(writeTaskHandle,"",rate,DAQmx_Val_Rising,DAQmx_Val_ContSamps,samples)
			
			DAQmxCreateTask("",byref(trigTaskHandle))
			DAQmxCreateAOVoltageChan(trigTaskHandle,trigChanID,"",vrange[0],vrange[1],DAQmx_Val_Volts,None)
			DAQmxCfgSampClkTiming(trigTaskHandle,"/"+self.devID+"/ao/SampleClock",rate,DAQmx_Val_Rising,DAQmx_Val_ContSamps,samples)
			
			DAQmxCreateTask("",byref(readTaskHandle))
			DAQmxCreateAIVoltageChan(readTaskHandle,readChanID,"",DAQmx_Val_Cfg_Default,vrange[0],vrange[1],DAQmx_Val_Volts,None)
			DAQmxCfgSampClkTiming(readTaskHandle,"/"+self.devID+"/ao/SampleClock",rate,DAQmx_Val_Rising,DAQmx_Val_ContSamps,samples)

			DAQmxWriteAnalogF64(writeTaskHandle,samples,0,10.0,DAQmx_Val_GroupByChannel,inData,None,None)
			DAQmxWriteAnalogF64(trigTaskHandle,samples,0,10.0,DAQmx_Val_GroupByChannel,trigData,None,None)			
			DAQmxStartTask(readTaskHandle)
			DAQmxStartTask(writeTaskHandle)
			DAQmxStartTask(trigTaskHandle)
			
			time.sleep(30)
			# DAQmxReadAnalogF64(readTaskHandle,samples,10.0,DAQmx_Val_GroupByChannel,outData,samples,byref(read),None)
	
			# print "Acquired %d points"%read.value
	
		except DAQError as err:
			print "DAQmx Error: %s"%err
		finally:
			if readTaskHandle:
				DAQmxStopTask(readTaskHandle)
				DAQmxClearTask(readTaskHandle)	
			if writeTaskHandle:
				DAQmxStopTask(writeTaskHandle)
				DAQmxClearTask(writeTaskHandle)
			if trigTaskHandle:
				DAQmxStopTask(trigTaskHandle)
				DAQmxClearTask(trigTaskHandle)
		# Go back to 0 after measure
		# if presetVoltage: self.setOutputVoltage(0.,writeChan,vrange)
		
		return outData

	def syncTrigRamp(self,Vpp=0.5,offset=0,samples=1000,readChan="ai0",writeChan="ao0",rate=10000,fig=None,ax=None):
		warnings.warn("deprecated", DeprecationWarning)
		inData = np.linspace(-Vpp/2.+offset,Vpp/2.+offset,samples)
		outData = self.syncReadWriteTrig(inData,readChan,writeChan,"ao1",(-10,10),rate)
		if fig != None:
			plt.figure(fig)
			ax = plt.gca()
		if ax != None:
			ax.plot(inData,outData)
			plt.show(block=False)
		return inData,outData
		
if __name__=='__main__':
	daq = NIUSB6259()