import numpy as np
import quantities as pq

grosPackageFactor = 44.05 * pq.gauss / pq.A

def convertVolt2Temp(voltage):
	return betaThermRes2Temp(convertVolt2Res(voltage))

def convertVolt2Res(voltage):
	return -voltage*60295.5/5.

def convertRes2Temp(resistance):
	amplitude = 54.101
	decay = 4033.8219
	intercept = 31.6135
	slope = -0.0011
	return amplitude*np.exp(-resistance/decay) + slope*resistance + intercept

def betaThermRes2Temp(resistance):
	return float((1/(((np.log(resistance/5000.))/3976.)+(1/298.)))-273.)
	
def computeNePressure(temperature,shift=None,freq=None):
	# Temperature in degC, shift or freq in Hz
	assert shift is not None or freq is not None
	if shift is None:
		shift = freq - 9192631770
	beta = 686			# Hz/Torr    from [Kozlova2011]
	delta = 0.266		# Hz/Torr.K
	gamma = -1.68e-3	# Hz/Torr.K**2
	T0 = 273.2			# K
	P0 = shift/(beta + delta*temperature + gamma*temperature**2)
	return P0*(temperature+T0)/(T0)
	
def computeShotNoiseLimit(contrast,power,fwhm):
	stab = fwhm/9192631770. * 1/(contrast*np.sqrt(power/(2*6.63e-34*3.351e14)))
	return stab

def magShift(magField):
	beta = 427.45 * pq.Hz/pq.gauss**2
	delta = beta*(magField**2)
	return 

def computeShift(refFit,testFit):
	CsExHFS = 1167.68 * pq.megahertz
	rp1 = refFit.params["p1_center"]
	rp2 = refFit.params["p2_center"]
	tp1 = testFit.params["p1_center"]
	tp2 = testFit.params["p2_center"]
	shift1 = -(tp1-rp1)*CsExHFS/(rp2-rp1) 	# Minus in front because frequency goes down
	shift2 = -(tp2-rp2)*CsExHFS/(rp2-rp1) 	# as the laser modulation voltage goes up.
	return [shift1,shift2]