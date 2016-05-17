import numpy as np
from lmfit.models import PolynomialModel, LinearModel, LorentzianModel, GaussianModel

def decimalSep(number):
	'{:,}'.format(number).replace(',',' ')

def fitPolynomial(x,y,order):
	model = PolynomialModel(order)
	pars = model.guess(y, x=x)
	out = model.fit(y, pars, x=x)
	# out.params.update({'order':order})
	print out.fit_report()
	return out
	
def polyFitFunc(fitOut,minimum,maximum,ptNumber=2):
	x = np.linspace(minimum,maximum,ptNumber)
	args = {}
	for i in range(0,len(fitOut.params)):
		args.update({'c'+str(i):fitOut.best_values['c'+str(i)]})
	yfitted =  fitOut.model.func(x=x,**args)
	return x, yfitted

def linFitStr(fitOut):
	textstr = '\n'.join([
				r"Intercept \num{%.1f} $\pm$ \num{%.1f} Hz"%(fitOut.best_values['c0'],fitOut.params['c0'].stderr),
				r"Shift from Cs hfs \num{%.1f} $\pm$ \num{%.1f} Hz"%(fitOut.best_values['c0']-9192631770,fitOut.params['c0'].stderr),
				r"Ne pressure eval. \num{%.4f} $\pm$ \num{%.4f} Torr"%((fitOut.best_values['c0']-9192631770)/700.,fitOut.params['c0'].stderr/700.)
				])
	return textstr
	
def fitLorentzian(x,y):
	signalGuess = max(y)-min(y)
	# centerGuess = x[np.argmax(y)]
	centerGuess = (max(x)+min(x))/2.
	span = max(x)-min(x)
	sigmaGuess = span/10.
	x_bg = np.concatenate((x[:10],x[10:]))
	y_bg = np.concatenate((y[:10],y[10:]))
	background  = LinearModel()
	pars = background.guess(y_bg, x=x_bg)
	peak = LorentzianModel()
	pars.update( peak.make_params())
	pars['center'].set(centerGuess)#,min=min(x),max=max(x))
	pars['sigma'].set(sigmaGuess,max=span/2.)
	pars['amplitude'].set(signalGuess*sigmaGuess*np.pi,min=0.00000001)
	pars.add('signal', expr='amplitude/(sigma*pi)')
	pars.add('background', expr='intercept+slope*center')
	pars.add('contrast', expr='amplitude/(sigma*pi*background)')
	pars.add('centerDoubled', expr='2*center')
	pars.add('shift', expr='2*center-9192631770')
	pars.add('fwhmDoubled', expr='4*sigma')
	model = peak + background
	init = model.eval(pars, x=x)
	out = model.fit(y, pars, x=x)
	#print out.fit_report()
	return init,out

def fitDoubleLorentzian(x,y) :
	signalGuess = 0.5*(max(y)-min(y))
	centerGuess = (max(x)+min(x))/2.
	span = max(x)-min(x)
	sigmaGuess = span/10.
	x_bg = np.concatenate((x[:10],x[10:]))
	y_bg = np.concatenate((y[:10],y[10:]))
	background  = LinearModel()
	pars = background.guess(y_bg, x=x_bg)
	
	peak1 = LorentzianModel(prefix="p1_")
	pars.update(peak1.make_params())
	pars['p1_center'].set(centerGuess,min=min(x),max=max(x))
	pars['p1_sigma'].set(sigmaGuess,max=span/2.)
	pars['p1_amplitude'].set(signalGuess*sigmaGuess*np.pi,min=0.00000001)
	pars.add('p1_signal', expr='p1_amplitude/(p1_sigma*pi)')
	pars.add('background', expr='intercept+slope*p1_center')
	pars.add('p1_contrast', expr='p1_amplitude/(p1_sigma*pi*background)')
	pars.add('p1_centerDoubled', expr='2*p1_center')
	pars.add('p1_shift', expr='2*p1_center-9192631770')
	pars.add('p1_fwhmDoubled', expr='4*p1_sigma')
	
	peak2 = LorentzianModel(prefix="p2_")
	pars.update(peak2.make_params())
	pars['p2_center'].set(centerGuess,min=min(x),max=max(x))
	pars.add('broadScale',value=2.0, min=1.9, max=100.0)
	pars['p2_sigma'].set(sigmaGuess*2,max=span/2.,expr='p1_sigma*broadScale')
	pars['p2_amplitude'].set(signalGuess*sigmaGuess*np.pi,min=0.00000001)
	pars.add('p2_signal', expr='p2_amplitude/(p2_sigma*pi)')
	pars.add('p2_contrast', expr='p2_amplitude/(p2_sigma*pi*background)')
	pars.add('p2_centerDoubled', expr='2*p2_center')
	pars.add('p2_shift', expr='2*p2_center-9192631770')
	pars.add('p2_fwhmDoubled', expr='4*p2_sigma')
	
	model = peak1 + peak2 + background
	init = model.eval(pars, x=x)
	out = model.fit(y, pars, x=x)
	print out.fit_report()
	return init,out
	
def fitTwoGaussians(x,y):
	background  = PolynomialModel(2)
	pars = background.make_params()
	peak1 = GaussianModel(prefix='p1_')
	pars.update( peak1.make_params())
	peak2 = GaussianModel(prefix='p2_')
	pars.update( peak2.make_params())
	# Guess some parameters from data to help the fitting
	span = max(x)-min(x)
	c1Guess = (y[-1]-y[0])/(x[-1]-x[0])
	c0Guess = y[0]-c1Guess*x[0]
	bgGuess = background.func(x=x,c0=c0Guess,c1=c1Guess,c2=0.)
	signalGuess=min(y-bgGuess)
	sigmaGuess = span/30.
	amplitudeGuess = signalGuess*(sigmaGuess*np.sqrt(2.0*np.pi))
	# Fit variables initialization
	
	# pars.add('splitting',0.0001,max=span)
	
	pars['c2'].set(0.,min=-0.000001,max=0.001)
	pars['c1'].set(c1Guess)
	pars['c0'].set(c0Guess)
	pars['p1_center'].set(min(x)+span*0.35,min=min(x),max=max(x))
	pars['p2_center'].set(min(x)+span*0.55,min=min(x),max=max(x))
	# pars['p2_center'].set(min(x)+span*0.65,expr='p1_center+splitting')
	pars['p1_amplitude'].set(amplitudeGuess,max=amplitudeGuess/10000.)
	pars['p2_amplitude'].set(amplitudeGuess,max=amplitudeGuess/10000.)
	pars['p1_sigma'].set(sigmaGuess, min=sigmaGuess/100.,max=sigmaGuess*10000.)
	pars['p2_sigma'].set(sigmaGuess, min=sigmaGuess/100.,max=sigmaGuess*10000.)
	#Add some useful parameters to evaluate
	pars.add('p1_signal', expr='p1_amplitude/(p1_sigma*sqrt(2.0*pi))')
	pars.add('p2_signal', expr='p2_amplitude/(p2_sigma*sqrt(2.0*pi))')
	pars.add('p1_contrast', expr='-p1_amplitude/(p1_sigma*sqrt(2.0*pi)*(c0+c1*p1_center+c2*p1_center**2))')
	pars.add('p2_contrast', expr='-p2_amplitude/(p2_sigma*sqrt(2.0*pi)*(c0+c1*p2_center+c2*p2_center**2))')
	pars.add('splitting',pars['p2_center']-pars['p1_center'],expr='p2_center-p1_center',min=0.00001)
	model = peak1 + peak2 + background
	init = model.eval(pars, x=x)
	out = model.fit(y, pars, x=x)
	# print out.fit_report()
	return init,out

def fitTwoLorentzians(x,y):
	background  = PolynomialModel(2)
	pars = background.make_params()
	peak1 = LorentzianModel(prefix='p1_')
	pars.update( peak1.make_params())
	peak2 = LorentzianModel(prefix='p2_')
	pars.update( peak2.make_params())
	# Guess some parameters from data to help the fitting
	span = max(x)-min(x)
	c1Guess = (y[-1]-y[0])/(x[-1]-x[0])
	c0Guess = y[0]-c1Guess*x[0]
	bgGuess = background.func(x=x,c0=c0Guess,c1=c1Guess,c2=0)
	signalGuess=min(y-bgGuess)
	sigmaGuess = span/50.
	amplitudeGuess = signalGuess*(sigmaGuess*np.pi)
	# Fit variables initialization
	pars.add('splitting',value=min(x)+span*0.56,min=0.0000001,max=max(x)-min(x))
	pars['c2'].set(0.)
	pars['c1'].set(c1Guess)
	pars['c0'].set(c0Guess)
	pars['p1_center'].set(min(x)+span*0.45,min=min(x),max=max(x))
	pars['p2_center'].set(min(x)+span*0.55,expr='p1_center+splitting')
	# pars['p2_center'].set(min(x)+span*0.55,min=min(x),max=max(x))
	pars['p1_amplitude'].set(amplitudeGuess,max=amplitudeGuess/100.)
	pars['p2_amplitude'].set(amplitudeGuess,max=amplitudeGuess/100.)
	pars['p1_sigma'].set(sigmaGuess, min=sigmaGuess/1000.,max=sigmaGuess*1000.)
	pars['p2_sigma'].set(sigmaGuess, min=sigmaGuess/1000.,max=sigmaGuess*1000.)
	#Add some useful parameters to evaluate
	pars.add('p1_signal', expr='p1_amplitude/(p1_sigma*pi)')
	pars.add('p2_signal', expr='p2_amplitude/(p2_sigma**pi)')
	pars.add('p1_contrast', expr='-p1_amplitude/(p1_sigma*pi*(c0+c1*p1_center+c2*p1_center**2))')
	pars.add('p2_contrast', expr='-p2_amplitude/(p2_sigma*pi*(c0+c1*p2_center+c2*p2_center**2))')
	model = peak1 + peak2 + background
	init = model.eval(pars, x=x)
	out = model.fit(y, pars, x=x)
	print out.fit_report()
	return init,out
	
def linFitFunc(fitOut,minimum,maximum,ptNumber=100):
	x = np.linspace(minimum,maximum,ptNumber)
	background  = LinearModel()
	bg = background.func(x=x,intercept=fitOut.best_values["intercept"],slope=fitOut.best_values["slope"])
	return x,bg
	
def lorFitFunc(fitOut,minimum,maximum,ptNumber=100,prefix=None):
	x = np.linspace(minimum,maximum,ptNumber)
	lorentzian = LorentzianModel()
	if prefix==None: params = fitOut.best_values
	else: params = getKeysWithoutPrefix(fitOut.best_values,prefix)
	lor = lorentzian.func(x=x,center=params["center"],sigma=params["sigma"],amplitude=params["amplitude"])
	return x, lor

def gaussFitFunction(fitOut,minimum,maximum,ptNumber=100,prefix=None):
	x = np.linspace(minimum,maximum,ptNumber)
	gaussian = GaussianModel()
	if prefix==None: params = fitOut.best_values
	else: params = getKeysWithoutPrefix(fitOut.best_values,prefix)
	gauss = gaussian.func(x=x,center=params["center"],sigma=params["sigma"],amplitude=params["amplitude"])
	return x, gauss
	
def lorFitStr(fitOut):
	textstr = '\n'.join([u"Lor. contrast %.2f %%"%(fitOut.params["contrast"].value*100),
						u"Lor. signal %.6f V"%(fitOut.params["signal"].value),
						u"Lor. FWHM %.0f Hz"%(fitOut.params['fwhmDoubled'].value),
						u"Lor. cent. {:,} Hz".format(fitOut.params['centerDoubled'].value).replace(',',' '),
						u"Shift %.0f Hz"%(fitOut.params['centerDoubled'].value-9192631770)
						])
	return textstr

def doubleLorFitStr(fitOut):
	textstr = '\n'.join([u"L1 contrast %.2f %%"%(fitOut.params["p1_contrast"].value*100),
						u"L1 signal %.6f V"%(fitOut.params["p1_signal"].value),
						u"L1 FWHM %.0f Hz"%(fitOut.params['p1_fwhmDoubled'].value),
						u"L1 cent. {:,} Hz".format(fitOut.params['p1_centerDoubled'].value).replace(',',' '),
						u"L1 Shift %.0f Hz"%(fitOut.params['p1_centerDoubled'].value-9192631770),
						u"L2 contrast %.2f %%"%(fitOut.params["p2_contrast"].value*100),
						u"L2 signal %.6f V"%(fitOut.params["p2_signal"].value),
						u"L2 FWHM %.0f Hz"%(fitOut.params['p2_fwhmDoubled'].value),
						u"L2 cent. {:,} Hz".format(fitOut.params['p2_centerDoubled'].value).replace(',',' '),
						u"L2 Shift %.0f Hz"%(fitOut.params['p2_centerDoubled'].value-9192631770)
						])
	return textstr
	
def addPrefixToKeys(dic,prefix):
	for key in dic.keys():
		dic[prefix+key] = dic.pop(key)

def getKeysWithoutPrefix(inDic,prefix):
	outDic = dict()
	for key in inDic.keys():
		if key.startswith(prefix):
			outDic.update({key.strip(prefix): inDic[key]})
	return outDic

def getValues(arrayOfDict):
	outdic = {}
	for key in arrayOfDict[0].keys():
		outdic.update({key: np.array([dic[key] for dic in arrayOfDict])})
	return outdic
	
def makeFitParamsDic(fitOut):
	paramsDic = {}
	for param in fitOut.params:
		paramsDic.update({param:{"value":float(fitOut.params[param].value),"stderr":float(fitOut.params[param].stderr)}})
	return paramsDic