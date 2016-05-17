from drivers.powerMeter import *
from drivers.stepper import *
import time,sys
sys.path.append("..")
from utils.calculs import *

class TempController(object):

	def __init__(self,multimeter,name=None):
		self.multimeter = multimeter
		self.name = name

	@property
	def temperature(self):
		return betaThermRes2Temp(self.multimeter.read())
	
	def getParams(self):
		params = dict()
		params.update({"measCellTemp":self.getTemperature()})
		return {self.name:params}