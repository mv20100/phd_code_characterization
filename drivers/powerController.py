from drivers.powerMeter import *
from drivers.stepper import *
from utils.misc import Buffer
import time,sys, threading
import numpy as np


class PowerGetter(threading.Thread):

	samp_num = 10

	def __init__(self,pow_ctrl):
			threading.Thread.__init__(self)
			self.daemon = True
			self.pow_ctrl = pow_ctrl
			self.buf = Buffer(self.samp_num)
			self.running = True

	def run(self):
		while self.running:
			self.buf.append(self.pow_ctrl.powmeter.power)
			time.sleep(0.01)

class PowerSetter(threading.Thread):

	timeout = 50
	gainL = 4.
	gainM = 0.8

	def __init__(self,pow_ctrl, startHolder=False):
		threading.Thread.__init__(self)
		self.daemon = True
		self.pow_ctrl = pow_ctrl
		self.running = True
		self.start_holder = startHolder
		
	def run(self):
		self.pow_ctrl.noise_eater_voltage = 3
		start_time = time.time()
		while self.running:
			last = self.pow_ctrl.powerGetter.buf.get_last()
			average = self.pow_ctrl.powerGetter.buf.get_average()
			std = self.pow_ctrl.powerGetter.buf.get_std()
			errorL = last - self.pow_ctrl.targetPower
			errorM = average - self.pow_ctrl.targetPower
			correction = errorL * self.gainL + errorM * self.gainM  #
			# print("correction {}, errorL {}, std {}".format(correction,errorL,std))
			if abs(errorL) <= 0.03 and std <= 0.03:
				print("Setpoint reached")
				if self.start_holder: self.pow_ctrl.holdPower()
				break
			self.actuateMotor(correction)
			if time.time() - start_time >= self.timeout:
				print("Timeout")
				if self.start_holder: self.pow_ctrl.holdPower()
				break
		self.running = False

	def actuateMotor(self,speed):
		delay = sorted([0., 1./abs(speed), 0.5])[1]
		# print("Speed {}, Delay {}".format(speed,delay))
		if speed>= 0:
			# print("Step L")
			self.pow_ctrl.stepper.oneStepL()
		else:
			# print("Step R")
			self.pow_ctrl.stepper.oneStepR()
		time.sleep(delay)

	def stop(self):
		self.running = False

class PowerHolder(threading.Thread):
	def __init__(self,pow_ctrl):
		threading.Thread.__init__(self)
		self.daemon = True
		self.pow_ctrl = pow_ctrl
		self.running = True
		
	def run(self):
		targetPower = self.pow_ctrl.targetPower
		if not targetPower:
			targetPower = self.pow_ctrl.powerGetter.buf.get_last()
		print("Starting power holder")
		while self.running:
			last = self.pow_ctrl.powerGetter.buf.get_last()
			average = self.pow_ctrl.powerGetter.buf.get_average()
			errorM = average - targetPower
			errorL = last - targetPower
			correction = errorL * self.pow_ctrl.holder_p_gain + errorM * self.pow_ctrl.holder_i_gain
			self.pow_ctrl.noise_eater_voltage -= correction
			# print("Voltage: {}, Correction: {}".format(currentVoltage,correction))
			time.sleep(0.1)

	def stop(self):
		self.running = False

class MeanSignalHolder(threading.Thread):
	def __init__(self,pow_ctrl):
		threading.Thread.__init__(self)
		self.daemon = True
		self.pow_ctrl = pow_ctrl
		self.running = True
		
	def run(self):
		buf = self.pow_ctrl.asserv.mean_buffer
		signal_set_point = buf.get_last()
		print("Starting mean signal holder")
		while self.running:
			last = buf.get_last()
			average = buf.get_average()
			errorM = average - signal_set_point
			errorL = last - signal_set_point
			correction = errorL * self.pow_ctrl.holder_p_gain + errorM * self.pow_ctrl.holder_i_gain
			self.pow_ctrl.noise_eater_voltage -= correction
			# print("Voltage: {}, Correction: {}".format(currentVoltage,correction))
			time.sleep(0.1)

	def stop(self):
		self.running = False

class PowerController(object):

	holder_methods = {"Power meter": PowerHolder, "Mean signal": MeanSignalHolder}
	selected_holder_method = PowerHolder

	def __init__(self,stepper,powmeter,noise_eater_supply,bsPowerRatio=1.,asserv=None,name="powerController"):
		self.stepper = stepper
		self.powmeter = powmeter
		self.noise_eater_supply = noise_eater_supply
		self.bsPowerRatio = bsPowerRatio
		self.asserv = asserv
		self.name = name
		self.powerSetter = None
		self.powerGetter = PowerGetter(self)
		self.powerGetter.start()
		self.powerHolder = None
		self.targetPower = None
		self.holder_p_gain = 1
		self.holder_i_gain = 0.5
		self._noise_eater_voltage = self.noise_eater_supply.voltage6V

	def getSelectedHolderMethod(self):
		for key, value in self.holder_methods.items():
			if value == self.selected_holder_method:
				return {key:value}

	def holdPower(self,power = None):
		if power:
			self.targetPower = power/self.bsPowerRatio
		self.powerHolder = self.selected_holder_method(self)
		self.powerHolder.start()

	def stopHolder(self):
		if self.powerHolder:
			self.powerHolder.stop()

	def setPower(self, power, blocking = True):
		if self.powerSetter:
			self.powerSetter.stop()
			self.powerSetter.join()
		power_holder_was_running = False
		if self.powerHolder:
			power_holder_was_running = self.powerHolder.running 
			self.powerHolder.stop()
			self.powerHolder.join()
		self.targetPower = power/self.bsPowerRatio
		self.powerSetter = PowerSetter(self,startHolder = power_holder_was_running)
		self.powerSetter.start()
		if blocking: self.powerSetter.join()
		
	@property
	def power(self):
		if self.powerGetter.running:
			return self.powerGetter.buf.get_last() * self.bsPowerRatio
		return self.powmeter.power * self.bsPowerRatio

	@power.setter
	def power(self, power):
		self.setPower(power, blocking = False)

	@property
	def noise_eater_voltage(self):
		if not self._noise_eater_voltage:
			self._noise_eater_voltage = self.noise_eater_supply.voltage6V
		return self._noise_eater_voltage

	@noise_eater_voltage.setter
	def noise_eater_voltage(self,voltage):
		if voltage != self._noise_eater_voltage:
			voltage = sorted([0.,voltage,6.])[1]		# Constrain the voltage between 0 and 6 V
			self.noise_eater_supply.voltage6V = voltage
			self._noise_eater_voltage = voltage