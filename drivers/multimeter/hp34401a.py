import visa

class HP34401A(object):

	mode_dc_voltage = "VOLT:DC"
	mode_resistance = "RES"

	def __init__(self,gpibAdress=2):
		gpibID = "GPIB::"+str(gpibAdress)+"::INSTR"
		rm = visa.ResourceManager()
		self.inst = rm.open_resource(gpibID,read_termination='\n')

	def send(self,command):
		self.inst.write(command)

	def query(self,command):
		self.send(command)
		return self.inst.read()

	def configure(self,mode=mode_dc_voltage,range=1,resolution=1e-6):
		self.send("CONF:{} {}, {}".format(str(mode),float(range),float(resolution)))

	def trig(self):
		self.send("TRIG:SOUR:IMM")
		self.send("TRIG:COUN 1")

	def init(self):
		self.send("INIT")

	def read(self):
		return float(self.query("READ?"))

	def fetch(self):
		return float(self.query("FETC?"))

	@property
	def resistance(self):
		return float(self.query("MEAS:RES?"))
	
	@property	
	def dc_voltage(self):
		return float(self.query("MEAS:VOLT:DC?"))


if __name__=='__main__':
	multimeter = HP34401A()