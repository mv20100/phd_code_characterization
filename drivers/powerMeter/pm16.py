import visa

class PM16(object):
	def __init__(self,powerMeterID="15110239"):
		devID = "USB0::0x1313::0x807B::"+powerMeterID+"::INSTR"
		rm = visa.ResourceManager()
		self.inst = rm.open_resource(devID,read_termination='\n')
		# self.inst.timeout = 10

	def query(self,command):
		self.inst.write(command)
		return self.inst.read()

	@property
	def id(self):
		return self.query("SYST:SENS:IDN?")

	@property
	def power(self):
		return float(self.query("MEAS:POW?"))*1e6
	
if __name__=='__main__':
	power_meter = PM16()