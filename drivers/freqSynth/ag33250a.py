import visa

FM_SOURCE_EXT = "ext"

class AG33250A(object):

	def __init__(self,gpibAdress=10,name=None):
		ddsID = "GPIB::"+str(gpibAdress)+"::INSTR"
		rm = visa.ResourceManager()
		self.name = name
		self.inst = rm.open_resource(ddsID,read_termination='\n')

	def send(self,command):
		self.inst.write(command)

	def query(self,command):
		self.inst.write(command)
		return self.inst.read()


	@property
	def frequency(self):
		return float(self.query("freq?"))

	@frequency.setter
	def frequency(self, value):
		self.send("freq {:.6f}".format(float(value)))

	@property
	def powerUnit(self):
		return str(self.query("volt:unit?"))

	@powerUnit.setter
	def powerUnit(self, value):
		self.send("volt:unit {}".format(str(value)))

	@property
	def power(self):
		if self.powerUnit == "dbm" :
			return float(self.query("volt?"))
		else :
			self.powerUnit = "dbm"
			return float(self.query("volt?"))

	@power.setter
	def power(self, value):
		self.powerUnit = "dbm"
		self.send("volt {:.6f}".format(float(value)))

	@property
	def vpp(self):
		if self.powerUnit == "vpp" :
			return float(self.query("volt?"))
		else :
			self.powerUnit = "vpp"
			return float(self.query("volt?"))

	@vpp.setter
	def vpp(self, value):
		self.powerUnit = "vpp"
		self.send("volt {:.6f}".format(float(value)))

	@property
	def fm_dev(self):
		return float(self.query("fm:dev?"))

	@fm_dev.setter
	def fm_dev(self,value):
		self.send("fm:dev {:.6f}".format(float(value)))

	@property
	def fm_source(self):
		return str(self.query("fm:sour?"))

	@fm_source.setter
	def fm_source(self,value):
		self.send("fm:sour {}".format(str(value)))

	@property
	def fm_status(self):
		return bool(int(self.query("fm:stat?")))

	@fm_status.setter
	def fm_status(self,value):
		self.send("fm:stat {}".format(int(value)))


	# def initialize(self):

	# 	"

if __name__ == "__main__":
	dds = AG33250A()