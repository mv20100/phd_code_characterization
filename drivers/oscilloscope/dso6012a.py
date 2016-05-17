import numpy as np
import matplotlib.pyplot as plt
import visa
import time
import math

class DSO6012A(object):

	def __init__(self):
		scopeID = "USB0::0x0957::0x1722::MY45002264::INSTR" # For DSO6012A
		#scopeID = "USB0::0x0957::0x1798::MY54231293::INSTR" # For DSO-X-2014A
		rm = visa.ResourceManager()
		self.inst = rm.open_resource(scopeID,read_termination='\n')

	def write(self,command):
		# print command	
		return self.inst.write(command)
	
	def getChanData(self,channel):
		self.write(":WAVEFORM:SOURCE CHAN"+str(int(channel)))
		self.write(":WAVEFORM:FORMAT ASCii")
		self.write(":WAVEFORM:DATA?")
		data = self.inst.read()
		numberOfDigit=int(data[1])
		data=data[numberOfDigit+3:]
		data = data.split(',')
		data = np.array(data)
		data = data.astype(np.float)
		return data
	
	def getWaveForm(self, channel):
		self.write(":DIGITIZE CHANNEL"+str(int(channel)))
		data = self.getChanData(channel)
		self.write("RUN")
		return data
		
	def getAllChanWF(self):
		self.write(":VIEW CHANNEL1;:VIEW CHANNEL2;:DIGITIZE")
		data1 = self.getChanData(1)
		data2 = self.getChanData(2)
		self.write("RUN")
		return data1,data2
	
	def getPointNumber(self):
		self.inst.write(":WAVEFORM:POINTS?")
		pointNumber = self.inst.read()
		pointNumber = int(pointNumber)
		return pointNumber
	
	def acquire(self,channel=None,plot=False,autoscale=True):
		
		if autoscale:
			if channel: self.myAutoScale(channel)
			else :
				self.myAutoScale(1)
				self.myAutoScale(2)
		
		x = self.getTimeRangeArray()
		if channel:
			y1 = self.getWaveForm(channel)
		else:
			y1,y2 = self.getAllChanWF()
		
		if plot:
			plt.plot(x,y1)
			if not channel: 
				plt.plot(x,y2)
			plt.show(block=False)
		
		if channel:
			table = np.eye(len(x),2)
		else: table = np.eye(len(x),3)
		table[:,0] = x
		table[:,1] = y1
		if not channel:
			table[:,2] = y2
		return table

	def getTimeRange(self):
		self.inst.write(":TIMEBASE:RANGE?")
		timerange = self.inst.read()
		timerange = float(timerange)
		return timerange
		
	def getTimeRangeArray(self):
		pointNumber = self.getPointNumber()
		timerange = self.getTimeRange()
		x = np.linspace(-timerange/2.,timerange/2.,pointNumber)
		return x
	
	def getRange(self, channel):
		self.inst.write(":CHANNEL"+str(int(channel))+":RANGE?")
		range = self.inst.read()
		range = float(range)
		print "getRange: "+str(range)
		return range
	
	def setRange(self,range,channel):
		print "Chan"+str(channel)+" setRange: "+str(range)
		self.inst.write(":CHANNEL"+str(int(channel))+":RANGE "+str(range))
		self.getRange(channel)
		return

	def getOffset(self, channel):
		self.inst.write(":CHANNEL"+str(int(channel))+":OFFSET?")
		offset = self.inst.read()
		offset = float(offset)
		print "getOffset: "+str(offset)
		return offset

	def setOffset(self,offset,channel):
		print "Chan"+str(channel)+" setOffset: "+str(offset)
		self.inst.write(":CHANNEL"+str(int(channel))+":OFFSET "+str(offset))
		return

	def getMinMax(self,channel):
		data = self.getWaveForm(channel)
		sigMin = min(data)
		sigMax = max(data)
		print "min: "+str(sigMin)+" max: "+str(sigMax)+" ampl: "+str(sigMax-sigMin)
		return sigMin, sigMax
		
	def getAverage(self,channel,autoscale=False):
		if autoscale: self.myAutoScale(channel)
		data = self.getWaveForm(channel)
		avg = np.mean(data)
		print "avg: "+str(avg)
		return avg
		
	def myAutoScale(self,channel):
		range = 4
		offset = 0
		
		self.setRange(range,channel)
		self.setOffset(offset,channel)
		
		sigMin, sigMax = self.getMinMax(channel)
		
		range = max(0.1,sigMax-sigMin) #Prevent from narrowing the range too soon
		offset = (sigMax+sigMin)/2
		self.setRange(range,channel)
		self.setOffset(offset,channel)
		sigMin, sigMax = self.getMinMax(channel)
		
		range = 1.2*math.ceil(1.2*(sigMax-sigMin)/0.008)*0.008 #Get the minimum range that fits the signal
		offset = (sigMax+sigMin)/2
		self.setRange(range,channel)
		self.setOffset(offset,channel)
		sigMin, sigMax = self.getMinMax(channel)
		
		offset = (sigMax+sigMin)/2
		self.setOffset(offset,channel)
		
		return
	
if __name__=='__main__':
	scope = DSO6012A()