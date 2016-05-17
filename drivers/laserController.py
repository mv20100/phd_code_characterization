from drivers.nidaq import *
import time
import matplotlib.pyplot as plt
import numpy as np

class LaserController(object):

	def __init__(self,daq,laserModChan="ao0",signalChan="ai0",lockBox=None,name=None):
		self.daq = daq
		self.signalChan = signalChan
		self.laserModChan = laserModChan
		self._dc_offset = None
		self.name = name
		self.lockBox = lockBox

	def goToMinAbsPeak(self,fig=None,delock=True):
		if delock:
			lockState = self.lockBox.lock
			self.lockBox.lock = False
			time.sleep(1)
		print "Looking for deepest abs. peak center"
		if fig is not None:
			plt.figure(fig)
			plt.clf()
		min,self.offsetDC = self.daq.getArgMin(readChan=self.signalChan,writeChan=self.laserModChan,Vpp=6,offset=self.offsetDC,rate=1000,samples=5000,fig=fig,filter=101)
		self.daq.setOutputVoltage(self.offsetDC,self.laserModChan,(-10,10))
		time.sleep(3)
		print "[DONE]"
		print "Found minimum of %f V at %f V"%(min,self.offsetDC)
		if delock:
			time.sleep(2)
			self.lockBox.lock = lockState
			time.sleep(1)
		return

	@property
	def dc_offset(self):
		if not self._dc_offset:
			self._dc_offset = np.round(self.daq.read_voltage_on_output(self.laserModChan),3)
		return self._dc_offset

	@dc_offset.setter
	def dc_offset(self,value):
		self._dc_offset = value
		self.daq.setOutputVoltage(self._dc_offset,self.laserModChan,(-10,10))