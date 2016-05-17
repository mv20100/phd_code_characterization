import visa

class E8254A(object):

	def __init__(self,gpibAdress=19,name=None,pow_amp_lim=28):
		freqSynthID = "GPIB::"+str(gpibAdress)+"::INSTR"
		rm = visa.ResourceManager()
		self.name = name
		self.inst = rm.open_resource(freqSynthID,read_termination='\n')
		self.pow_amp_lim = pow_amp_lim

	def query(self,command):
		self.inst.write(command)
		return self.inst.read()

	def send(self,command):
		self.inst.write(command)

	@property
	def fm_dev(self):
		return float(self.query("FM:DEV?"))

	@fm_dev.setter
	def fm_dev(self,fmDev):
		self.send("FM:DEV "+str(fmDev))
		
	@property
	def frequency(self):
		return float(self.query("FREQ:CW?"))
	
	@frequency.setter
	def frequency(self,freq):
		self.send("FREQ:CW "+str(freq))

	@property
	def power_amplitude(self):
		return float(self.query("POW:AMPL?"))

	@power_amplitude.setter
	def power_amplitude(self,pow):
		assert pow<=self.pow_amp_lim
		self.send("POW:AMPL "+str(pow))
		
	@property
	def rf_state(self):
		return bool(int(self.query("OUTP:STAT?")))

	@rf_state.setter
	def rf_state(self,state):
		self.send("OUTP:STAT "+str(int(bool(state))))

	@property
	def fm_state(self):
		return bool(int(self.query("FM:STAT?")))

	@fm_state.setter
	def fm_state(self,state):
		self.send("FM:STAT "+str(int(bool(state))))

	@property
	def mod_state(self):
		return bool(int(self.query("OUTP:MOD:STAT?")))
	
	@mod_state.setter
	def mod_state(self,state):
		self.send("OUTP:MOD:STAT "+str(int(bool(state))))

	@property
	def fm_ext1_coupling(self):
		return self.query("FM:EXT1:COUP?")
	
	def getParams(self):
		params = dict()
		params.update({"RFstate":self.rf_state})
		params.update({"FMstate":self.fm_state})
		params.update({"Modstate":self.mod_state})
		params.update({"RFpow":self.power_amplitude})
		params.update({"fmDev":self.fm_dev})
		params.update({"fmCoup":self.fm_ext1_coupling})
		return {self.name:params}
		
if __name__=='__main__':
	freqSynth = E8254A()