import visa

class HP53132A(object):

	def __init__(self,gpibAdress=25):
		gpibID = "GPIB::"+str(gpibAdress)+"::INSTR"
		rm = visa.ResourceManager()
		self.inst = rm.open_resource(gpibID,read_termination='\n')

	def getFunction(self):
		self.inst.write("FUNC?")
		function = self.inst.read()
		return function

	def setFunction(self,function):
		self.inst.write("FUNC "+str(function))
		return

	def setConfig(self,delay=1):
		request = ":func 'freq 1';:freq:arm:star:sour imm;:freq:arm:stop:sour tim;:freq:arm:stop:tim "+str(delay)
		self.inst.write(request)
		return
	
	def getFrequency(self):
		self.inst.write("READ:FREQ?")
		frequency = float(self.inst.read())
		return frequency
	
if __name__=='__main__':
	counter = HP53132A()