import time,sys, threading
from drivers.nidaq import *
from drivers.lockBox import *
from utils.misc import Buffer
import matplotlib.pyplot as plt
import numpy as np

class CarrierSignalGetter(threading.Thread):

	samp_num = 20

	def __init__(self,bias_ctrl):
			threading.Thread.__init__(self)
			self.daemon = True
			self.bias_ctrl = bias_ctrl
			self.buf = Buffer(self.samp_num)
			self.running = False

	def run(self):
		self.running = True
		while self.running:
			self.buf.append(self.bias_ctrl.vmeter.read())
			time.sleep(0.1)

	def get_last(self):
		return self.buf.get_data()[-1]

	def get_average(self):
		return np.mean(self.buf.get_data())

	def get_std(self):
		return np.std(self.buf.get_data())

class CarrierSignalCanceller(threading.Thread):

	def __init__(self,bias_ctrl):
		threading.Thread.__init__(self)
		self.daemon = True
		self.bias_ctrl = bias_ctrl
		self.running = False
		
	def run(self):
		print("Starting carrier canceller")
		self.running = True
		targetVoltage = 0.0
		while self.running:
			last = self.bias_ctrl.carrierSignalGetter.get_last()
			average = self.bias_ctrl.carrierSignalGetter.get_average()
			errorM = average - targetVoltage
			errorL = last - targetVoltage
			correction = errorL * self.bias_ctrl.canceller_p_gain + errorM * self.bias_ctrl.canceller_i_gain
			self.bias_ctrl.dc_bias += correction
			# print("Voltage: {}, Correction: {}".format(currentVoltage,correction))
			time.sleep(0.5)

	def stop(self):
		self.running = False

class BiasController(object):

	canceller_p_gain = 10
	canceller_i_gain = 5

	def __init__(self,daq,biasChan="ao1",signalChan="ai0",name=None,lockBox=None,voltmeter=None):
		self.daq = daq
		self.signalChan = signalChan
		self.biasChan = biasChan
		self._dc_bias = None
		self.lockBox = lockBox
		self.vmeter = voltmeter
		self.name = name
		self.carrierSignalGetter = CarrierSignalGetter(self)
		self.carrierSignalGetter.start()
		self.carrierSignalCanceller = None

	# def carrierSuppression(self,fig=None,delock=True):
	# 	if delock:
	# 		lockState = self.lockBox.lock
	# 		self.lockBox.lock = False
	# 		time.sleep(1)
	# 	print "Looking for DC bias minimizing signal"
	# 	if fig is not None:
	# 		plt.figure(fig)
	# 		plt.clf()
	# 	min,self.biasDC = self.daq.getArgMin(readChan=self.signalChan,writeChan=self.biasChan,Vpp=6,offset=self.biasDC,samples=10000,rate=1000,fig=fig,filter=101)
	# 	# self.daq.setOutputVoltage(self.biasDC,self.biasChan,(-10,10))
	# 	print "[DONE]"
	# 	print "Found minimum of %f V at %f V"%(min,self.biasDC)
	# 	if delock:
	# 		time.sleep(2)
	# 		self.lockBox.lock = lockState
	# 		time.sleep(1)
	# 	return

	@property
	def dc_bias(self):
		if not self._dc_bias:
			self._dc_bias = np.round(self.daq.read_voltage_on_output(self.biasChan),3)
		return self._dc_bias

	@dc_bias.setter
	def dc_bias(self,value):
		self._dc_bias = value
		self.daq.setOutputVoltage(self._dc_bias,self.biasChan,(-10,10))

	@property
	def carrier_signal(self):
		if self.carrierSignalGetter.running:
			return self.carrierSignalGetter.get_last()
		return self.vmeter.read()

	def start_canceller(self):
		self.carrierSignalCanceller = CarrierSignalCanceller(self)
		self.carrierSignalCanceller.start()

	def stop_canceller(self):
		if self.carrierSignalCanceller:
			self.carrierSignalCanceller.stop()