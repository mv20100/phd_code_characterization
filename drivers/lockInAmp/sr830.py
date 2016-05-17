import visa
import time
import numpy as np

sensitivities = [2e-9,5e-9,1e-8,2e-8,5e-8,1e-7,2e-7,5e-7,1e-6,2e-6,5e-6,
				1e-5,2e-5,5e-5,1e-4,2e-4,5e-4,1e-3,2e-3,5e-3,1e-2,2e-2,5e-2,
				1e-1,2e-1,5e-1,1] # in volt
timeConstants = [1e-5,3e-5,1e-4,3e-4,1e-3,3e-3,1e-2,3e-2,0.1,0.3,1,3,10,30,1e2,3e2,1e3,3e3,1e4,3e4] # in second
sampleRates = [62.5e-3,125e-3,250e-3,500e-3,1,2,4,8,16,32,64,128,256,512,"Trigger"]
lowPassFiltSlopes = [6,12,18,24] # in dB/oct
inputConfigs = ["A","A-B","I (1 Mohm)","I (100 Mohm)"]
inputShieldGrounds = ["Float","Ground"]
inputCouplings = ["AC","DC"]
lineNotchFilters = ["Out","Line In","2xLine In","Both In"]
locRemStates = ["LOCAL","REMOTE","LOCAL LOCKOUT"]

class SR830(object):

	def __init__(self,gpibAdress=8,name=None):
		gpibID = "GPIB::"+str(gpibAdress)+"::INSTR"
		rm = visa.ResourceManager()
		self.inst = rm.open_resource(gpibID,read_termination='\n')
		self.name = name
		self.overide_rem_state = 0
		self.loc_rem_state = 1

	def send(self,command):
		self.inst.write(command)

	def query(self,command):
		self.send(command)
		return self.inst.read()

	#REFERENCE		
	@property
	def amplitude(self):
		return float(self.query("SLVL?"))

	@amplitude.setter
	def amplitude(self,amplitude):
		self.send("SLVL "+str(amplitude))

	@property
	def phase(self):
		return float(self.query("PHAS?"))

	@phase.setter
	def phase(self,phase):
		self.send("PHAS "+str(phase))

	@property
	def ref_freq(self):
		return float(self.query("FREQ?"))

	@ref_freq.setter
	def ref_freq(self,freq):
		self.send("FREQ "+str(freq))

	def getOutputX(self,iterations=1,timeit=False):
		value = 0.
		startT = time.time()
		for i in range(iterations):
			self.inst.write("OUTP?1")
			value = value + float(self.inst.read())
		if timeit: print "Duration: "+str(time.time()-startT)
		value = value/iterations
		return value
	
	def getOutputX2(self,sampleRateIdx=8,timeit=False,samples=25):
		startT = time.time()
		self.inst.write("SRAT "+str(int(sampleRateIdx))+";SEND 0")
		self.inst.write("REST;STRT")
		while self.getSamplePoints()<samples:
			time.sleep(0.01)
		self.inst.write("PAUS")
		self.inst.write("TRCA?1,0,"+str(int(samples)))
		buffer = self.inst.read()
		if timeit: print "Duration: "+str(time.time()-startT)
		return np.mean(np.array(buffer.split(',')[:-1],dtype=np.float))
		
	#INPUT and FILTER
	@property
	def input_config(self):
		inputConfigIdx = int(self.query("ISRC?"))
		return inputConfigs[inputConfigIdx]
	
	@input_config.setter
	def input_config(self,inputConfig):
		self.send("ISRC "+str(inputConfig))

	@property
	def input_shield_ground(self):
		inputShieldGroundIdx = int(self.query("IGND?"))
		return inputShieldGrounds[inputShieldGroundIdx]

	@input_shield_ground.setter
	def input_shield_ground(self,inputShieldGround):
		self.send("IGND "+str(inputShieldGround))
		
	@property
	def input_coupling(self):
		inputCouplingIdx = int(self.query("ICPL?"))
		return inputCouplings[inputCouplingIdx]
	
	@input_coupling.setter
	def input_coupling(self,inputCoupling):
		self.send("ICPL "+str(inputCoupling))

	@property
	def line_notch_filter(self):
		lineNotchFilterIdx = int(self.query("ILIN?"))
		return lineNotchFilters[lineNotchFilterIdx]
	
	@line_notch_filter.setter
	def line_notch_filter(self,lineNotchFilter):
		self.send("ILIN "+str(lineNotchFilter))
		
	#GAIN and TIME CONSTANT
	
	@property
	def sensitivity(self):
		sensitivityIdx = int(self.query("SENS?"))
		return sensitivities[sensitivityIdx]
		
	@sensitivity.setter
	def sensitivity(self,sensitivity):
		self.send("SENS "+str(sensitivity))

	@property
	def time_constant(self):
		timeConstantIdx = int(self.query("OFLT?"))
		return timeConstants[timeConstantIdx]
		
	@time_constant.setter
	def time_constant(self,timeConstant):
		self.send("OFLT "+str(timeConstant))

	@property
	def lowpass_filter_slope(self):
		lowPassFiltSlopeIdx = int(self.query("OFSL?"))
		return lowPassFiltSlopes[lowPassFiltSlopeIdx]
	
	@lowpass_filter_slope.setter
	def lowpass_filter_slope(self,lowPassFiltSlope):
		self.send("OFSL "+str(lowPassFiltSlope))
		
	# DATA TRANSFER COMMANDS
	@property
	def sample_points(self):
		return int(self.query("SPTS?"))
		
	# INTERFACE
	@property
	def loc_rem_state(self):
		locRemStateIdx = int(self.query("LOCL?"))
		return locRemStates[locRemStateIdx]

	@loc_rem_state.setter
	def loc_rem_state(self,locRemState):
		self.send("LOCL "+str(locRemState))

	@property
	def overide_rem_state(self):
		return int(self.query("OVRM?"))

	@overide_rem_state.setter
	def overide_rem_state(self,overideRemState):
		self.send("OVRM "+str(int(overideRemState)))

	def getParams(self):
		params = dict()
		params.update({"lowPassFiltSlope":self.getLowPassFiltSlope()})
		params.update({"timeConstant":self.getTimeConstant()})
		params.update({"sensitivity":self.getSensitivity()})
		params.update({"lineNotchFilter":self.getLineNotchFilter()})
		params.update({"inputCoupling":self.getInputCoupling()})
		params.update({"inputShieldGround":self.getInputShieldGround()})
		params.update({"inputConfig":self.getInputConfig()})
		params.update({"refFreq":self.getRefFreq()})
		params.update({"amplitude":self.getAmplitude()})
		params.update({"phase":self.getPhase()})
		return {self.name:params}
		
if __name__=='__main__':
	lockIn = SR830()