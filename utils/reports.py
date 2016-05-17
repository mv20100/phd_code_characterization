import os, glob, time,sys
from matplotlib import pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib import rc
import numpy as np
from misc import *
from fitting import *
from calculs import *
import paramFormater as paf

textBoxFontSize = 10


def makeColor(progress):
	return (progress,0,1-progress)

def getFilelist(argv,extension="(Freq).csv"):
	#Check that at least one filename is passed
	filelist = []
	if len(argv)==1:
		print "No file path given (taking all csv in current dir)"
		return glob.glob("*"+extension)
	if os.path.isdir(argv[1]):
		print "Dir path OK"
		return glob.glob(argv[1]+"\*"+extension)
	if os.path.isdir(argv[1]):
			print "Dir path OK"
			return glob.glob(argv[1]+"\*"+extension)
	for arg in argv[1:]:
		print arg
		if os.path.isfile(arg) and extension in arg:
			print "File path OK"
			filelist.append(arg)
	return filelist	

def makeTime(params):
	return time.mktime(time.strptime(params["date"]+" "+params["time"],"%d-%m-%y %H%M"))

def getTime(filename):
	params = readHeader(filename)
	measTime = makeTime(params)
	return measTime
	
# Sort file names according to time and date
def sortFilesByTime(filenames):
	times = []
	for idx, filename in enumerate(filenames):
		printProgress(idx,filenames,filename,message="Sorting files")
		times.append(getTime(filename))
	printDone()
	order = np.argsort(times)
	sortedFilenames = np.array(filenames)[order]
	return sortedFilenames

def scanFreqReport(filename,fitLor=True,fitDoubleLor=True,saveResults=True,fig=0,multipage=None,saveEachFig=False):
	print "Reading file "+filename
	params = readHeader(filename)
	measTime = makeTime(params)
	params.update({"floatTime":measTime})
	data = np.loadtxt(filename,delimiter=',')
	fitParams = dict()
	if fig is not None:
		plt.figure(fig,figsize=(10,8))
		plt.clf()
		ax1 = plt.gca()
		plt.plot(data[:,0],data[:,1],'k')
		textstr = paf.formatParams([paf.cell,paf.cellTemp,paf.intMagField,paf.date,paf.time,paf.cellTempCtrl_measCellTemp],params.copy())
	
	if fitLor:
		init, out = fitLorentzian(data[:,0],data[:,1])
		fitParams.update({"lorentzian":out.params})
		# fitParams.update({"lorentzian":makeFitParamsDic(out)})
		if fig is not None:	
			plt.plot(data[:,0],out.best_fit,color='red')
			plt.plot(data[:,0],init,'--',color='orange')
			textstr = '\n'.join([textstr,lorFitStr(out)])
	
	if fitDoubleLor:
		init, out = fitDoubleLorentzian(data[:,0],data[:,1])
		# fitParams.update({"doubleLorentzian":makeFitParamsDic(out)})
		fitParams.update({"doubleLorentzian":out.params})
		if fig is not None:
			plt.plot(data[:,0],out.best_fit,color='blue')
			plt.plot(data[:,0],init,'--',color='teal')
			x, background = linFitFunc(out,min(data[:,0]),max(data[:,0]),ptNumber=100)
			x, peak1 = lorFitFunc(out,min(data[:,0]),max(data[:,0]),ptNumber=100,prefix="p1_")
			x, peak2 = lorFitFunc(out,min(data[:,0]),max(data[:,0]),ptNumber=100,prefix="p2_")
			plt.plot(x, peak1+background,'--',color='indigo')
			plt.plot(x, peak2+background,'--',color='green')
			textstr = '\n'.join([textstr,doubleLorFitStr(out)])
	
	params.update({"fitParams":fitParams})
	if fig is not None:
		ax1.text(0.05, 0.95, textstr, transform=ax1.transAxes,verticalalignment='top',horizontalalignment='left',fontsize=textBoxFontSize)
		plt.title(os.path.basename(filename))
		plt.show(block=False)
		if saveEachFig: plt.savefig(filename.replace(".csv",".png"))
		if multipage: multipage.savefig()
	
	if saveResults:
		# saveYaml(params,filename=filename.replace(".csv","(FitParams).yaml"))
		savePickle(params,filename=filename.replace(".csv","(FitParams).pkl"))
	
	return params

def plotParam(dicArr,xparam,yparam,xlabel=None,ylabel=None,legend=False,label=None,linestyle='--'):
	if xlabel: plt.xlabel(xlabel)
	elif type(xparam) is paf.Parameter: plt.xlabel(xparam.longAxisLabel())
	if ylabel: plt.ylabel(ylabel)
	elif type(yparam) is paf.Parameter: plt.ylabel(yparam.longAxisLabel())
	
	if legend and not label:
		label = yparam.shortAxisLabel()
	
	if hasattr(dicArr[yparam.getLongName()][0],"value"):
		plt.errorbar(dicArr[xparam.getLongName()], [x.value for x in dicArr[yparam.getLongName()]],yerr=[x.stderr for x in dicArr[yparam.getLongName()]], fmt='',marker='.',linestyle=linestyle)
	else:
		plt.plot(dicArr[xparam.getLongName()], dicArr[yparam.getLongName()],marker='.',linestyle=linestyle,label=label)
	if legend:
		plt.legend(frameon=False,prop={'size':10})
