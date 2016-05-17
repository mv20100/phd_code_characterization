import visa

class E3631A(object):

	current_limit = 1.

	def __init__(self,gpibAdress=5,name=None):
		powSupID = "GPIB::"+str(gpibAdress)+"::INSTR"
		rm = visa.ResourceManager()
		self.name = name
		self.inst = rm.open_resource(powSupID,read_termination='\n')

	def query(self,command):
		self.inst.write(command)
		return self.inst.read()

	def send(self,command):
		self.inst.write(command)

	@property
	def output_sate(self):
		return bool(int(self.query("OUTP:STAT?")))

	@output_sate.setter
	def output_sate(self,state):
		self.send("OUTP:STAT " +str(int(state)))

	@property
	def voltage6V(self):
		resp = self.query("APPL? P6V")
		array = resp[1:-1].split(",")
		return float(array[0])

	@voltage6V.setter
	def voltage6V(self,voltage):
		self.send("APPL P6V, {:.4f}, {:.4f}".format(voltage,self.current_limit))
		
if __name__=='__main__':
	powSupply = E3631A()