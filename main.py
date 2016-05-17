import time, sys, inspect
from operator import attrgetter
import numpy as np
from utils.calculs import *
from utils.misc import loadYaml
from tasks.datalog import *
from tasks.fitter import *
import tasks.automation

print "Loading pyqtgraph",
import pyqtgraph as pg
from pyqtgraph.dockarea import *
from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph.parametertree.parameterTypes as pTypes
from ui.pyqtgraphaddon import MyFloatParameter
from pyqtgraph.parametertree import Parameter, ParameterTree
print " [DONE]"

print "Loading drivers",
from drivers import *
from drivers.nidaq.asserv import Asserv
from drivers.nidaq.syncAIAO import *
print " [DONE]"

constantParams = loadYaml('params.yaml')
data_folder_path = "G:\eric.kroemer\Desktop\Vincent\Pilotage Data"

class DeviceSet(object):
	def __init__(s):
		#Setup equipments
		print "Connecting to devices",
		s.daq = NIUSB6259(devID='Dev2')
		s.stepper = Stepper(comPort='com15')
		s.lock_box = LockBox(comPort='com13')
		s.regulation = CYPidReg(comPort='com21')
		s.regulation.configure(setpoint=75)
		s.pow_meter = PM16()
		s.fs = E8254A(gpibAdress=19,name="freqSynth")
		s.nois_eat_sup = E3631A(gpibAdress=5)
		# s.li_cpt = SR830(gpibAdress=8,name="cptLockIn")
		s.li_las = SR830(gpibAdress=9,name="laserLockIn")
		s.mag_cur_source = NP560B()
		s.multimeter1 = HP34401A(gpibAdress=2)
		s.multimeter3 = HP34401A(gpibAdress=24)
		s.vmeter_carrier = HP34401A(gpibAdress=16)
		s.vm_las_cur_mod = HP34401A(gpibAdress=10)
		s.multimeter1.configure(mode=HP34401A.mode_dc_voltage,range=10,resolution=1e-4)
		s.multimeter3.configure(mode=HP34401A.mode_resistance,range=10000,resolution=1e-1)
		s.vmeter_carrier.configure(mode=HP34401A.mode_dc_voltage,range=0.1,resolution=1e-6)
		s.vm_las_cur_mod.configure(mode=HP34401A.mode_dc_voltage,range=10,resolution=1e-4)

		#Setup compound equipments
		s.asserv = Asserv(device="Dev2",outChan="ao2",inChan="ai0",dds_device=s.fs)
		s.powCtrl = PowerController(s.stepper,s.pow_meter,s.nois_eat_sup,bsPowerRatio=203./180.,asserv=s.asserv,name="powerController") # bsPowerRatio = power at PP input / measured power
		s.biasCtrl = BiasController(s.daq,biasChan="ao1",signalChan="ai0",name="eomBiasCtrl",lockBox=s.lock_box,voltmeter=s.vmeter_carrier)
		s.laserCtrl = LaserController(s.daq,laserModChan="ao0",signalChan="ai0",name="laserCtrl",lockBox=s.lock_box)
		s.tempCtrl = TempController(s.multimeter3,name="Room thermometer")
		print " [DONE]"

		s.syncAiAo = SyncAIAO(inChanList=["ai0"],outChan="ao2",inRange=(-1.,1.),outRange=(-1.,1.))

		s.laserSyncAiAo = SyncAIAO(inChanList=["ai0","ai2"],outChan="ao0",inRange=(-10.,10.),outRange=(-10.,10.))
		s.laserSyncAiAo.vpp=8
		s.laserSyncAiAo.numSamp=4000
		s.laserSyncAiAo.nbSampCropped=2000 


class DataLogger(object):

	def __init__(self):

		self.consThread = None
		self.asservConsThread = None
		self.running = False

	def __del__(self):
		self.stop()

	def start(self):
		assert not self.running
		self.running = True

		timeStr = time.strftime("%Y-%m-%d %H%M")
		self.f1 = open("{}\datalog {} A.txt".format(data_folder_path,timeStr),'w')
		self.f2 = open("{}\datalog {} B.txt".format(data_folder_path,timeStr),'w')

		# Init producer thread
		aux_columns = [["Time",time.time],
						["Power meter (uW)",(a.powCtrl,'power')],
						["Cell temperature (degC)",(a.regulation,'temperature')],
						["Ext temperature (degC)",(a.tempCtrl,'temperature')],
						["Noise eater DC (V)",(a.powCtrl,'noise_eater_voltage')],
						["Heater current (A)",a.multimeter1.read],
						["Carrier signal (V)",(a.biasCtrl,'carrier_signal')],
						["EOM DC bias (V)",(a.biasCtrl,'dc_bias')],
						["Laser current modulation signal (V)",a.vm_las_cur_mod.read]]
		
		aux_headers = [item[0] for item in aux_columns]
		aux_getters = [item[1] for item in aux_columns]
		self.prodThread = DataProducer(aux_headers, aux_getters)

		# Init and start consumer threads
		self.consThread = DataConsumer(self.f1,self.prodThread.header)
		self.asservConsThread = DataConsumer(self.f2,a.asserv.header)
		self.consThread.start()
		self.asservConsThread.start()

		# Start producer threads
		self.prodThread.start()
		a.asserv.dataQueue = self.asservConsThread.data.queue
		self.prodThread.queue = self.consThread.data.queue

	def stop(self):
		if self.running:
			self.running = False
			self.consThread.stop()
			self.asservConsThread.stop()
			self.prodThread.stop()
			a.asserv.dataQueue = None
			self.f1.close()
			self.f2.close()

	def empty(self):
		self.consThread.empty()
		self.asservConsThread.empty()

class ControlWidget(pg.LayoutWidget):

	task = None

	def __init__(self, window=None):
		super(ControlWidget, self).__init__(window)
		self.window = window
		self.startLaserScanBtn = QtGui.QPushButton()
		self.startLaserScanBtn.setText("Start Laser Scan")
		self.startLaserScanBtn.setCheckable(True)
		self.startFreqScanBtn = QtGui.QPushButton()
		self.startFreqScanBtn.setText("Start Frequency Scan")
		self.startFreqScanBtn.setCheckable(True)
		self.startAsservBtn = QtGui.QPushButton()
		self.startAsservBtn.setText("Start Asserv")
		self.startAsservBtn.setCheckable(True)
		self.startDlBtn = QtGui.QPushButton()
		self.startDlBtn.setText("Start Data Logging")
		self.startDlBtn.setCheckable(True)

		self.startLaserScanBtn.clicked.connect(self.on_startLaserScanBtn)
		self.startFreqScanBtn.clicked.connect(self.on_startFreqScanBtn)
		self.startAsservBtn.clicked.connect(self.on_startAsservBtn)
		self.startDlBtn.clicked.connect(self.on_startDlBtn)

		gp0 = pTypes.GroupParameter(name='Constant parameters')
		self.cellName = Parameter.create(name='Cell ID', type='str',value=constantParams['cell'])
		gp0.addChildren([self.cellName])

		gsp1 = pTypes.GroupParameter(name='Equipments')

		gp1 = pTypes.GroupParameter(name='Laser Lock In')
		self.laserLockParam = Parameter.create(name='Lock', type='bool', value=a.lock_box.lock)
		self.laser_dc_offset_param = Parameter.create(name='DC offset', type='float', value=a.laserCtrl.dc_offset, step= 0.01, suffix='V')
		self.laserLockInAmp = Parameter.create(name='Amplitude', type='float', value=a.li_las.amplitude, step= 0.01, suffix='V',siPrefix=True)
		self.laserLockInPhase = Parameter.create(name='Phase', type='float', value=a.li_las.phase, step= 1, suffix='deg')
		self.laserLockInFreq = Parameter.create(name='Frequency', type='float', value=a.li_las.ref_freq, step= 1, suffix='Hz')
		gp1.addChildren([self.laserLockParam,self.laser_dc_offset_param,self.laserLockInAmp,self.laserLockInPhase,self.laserLockInFreq])

		gp2 = pTypes.GroupParameter(name='Frequency synthesis')
		self.fs_freq_param = MyFloatParameter.create(name='Frequency', type='float2', value=a.fs.frequency, step = 1000, suffix='Hz')
		self.fs_pow_amp_param = Parameter.create(name='Power', type='float', value=a.fs.power_amplitude, step = 0.1, suffix='dBm')
		self.fs_fm_dev_param = Parameter.create(name='FM dev', type='float', value=a.fs.fm_dev, step = 100, suffix='Hz', siPrefix=True)
		self.fs_freq_offset_action = Parameter.create(name='Frequency step', type='action')
		self.fs_freq_offset_value = Parameter.create(name='Offset', type='float', value=20, step = 1, suffix='Hz')
		self.fs_freq_offset_action.addChild(self.fs_freq_offset_value)
		gp2.addChildren([self.fs_freq_param,self.fs_pow_amp_param, self.fs_fm_dev_param,self.fs_freq_offset_action])

		gp3 = pTypes.GroupParameter(name='Magnetic field')
		self.mag_cur_out_param = Parameter.create(name='Ouput', type='bool', value=a.mag_cur_source.output)
		self.mag_cur_int_param = Parameter.create(name='Current', type='float', value=a.mag_cur_source.current_set_point, step = 0.1, suffix='mA')
		gp3.addChildren([self.mag_cur_out_param,self.mag_cur_int_param])	

		gp4 = pTypes.GroupParameter(name='EOM')
		self.eom_dc_bias_param = Parameter.create(name='DC bias', type='float', value=a.biasCtrl.dc_bias, step= 0.01, suffix='V')
		self.eom_dc_bias_lock_param = Parameter.create(name='Bias lock', type='bool', value=False)
		self.canceller_p_gain_param = Parameter.create(name='Canceller P gain', type='float', value=a.biasCtrl.canceller_p_gain, step= 0.01)
		self.canceller_i_gain_param = Parameter.create(name='Canceller I gain', type='float', value=a.biasCtrl.canceller_i_gain, step= 0.01)
		gp4.addChildren([self.eom_dc_bias_param,self.eom_dc_bias_lock_param,self.canceller_p_gain_param,self.canceller_i_gain_param])

		gp5 = pTypes.GroupParameter(name='Power')
		self.opt_pow_param = Parameter.create(name='Optical power set point', type='float', value=round(a.powCtrl.power,1), step= 1, suffix='uW')
		self.nois_eat_param = Parameter.create(name='Noise eater DC', type='float', value=a.powCtrl.noise_eater_voltage, step= 0.01, suffix='V')
		self.pow_holder_param = Parameter.create(name='Power holder', type='bool', value=False)
		self.pow_holder_method_param = Parameter.create(name='Pow. hold. method', type='list', value=a.powCtrl.getSelectedHolderMethod(), values=a.powCtrl.holder_methods)
		self.holder_p_gain_param = Parameter.create(name='Holder P gain', type='float', value=a.powCtrl.holder_p_gain, step= 0.01)
		self.holder_i_gain_param = Parameter.create(name='Holder I gain', type='float', value=a.powCtrl.holder_i_gain, step= 0.01)
		gp5.addChildren([self.opt_pow_param,self.nois_eat_param,self.pow_holder_param,self.pow_holder_method_param,self.holder_p_gain_param,self.holder_i_gain_param])

		gp6 = Parameter.create(name='CPT Detection', type='group')
		self.cpt_lock_param = Parameter.create(name='Lock', type='bool', value=a.asserv.lock)
		self.gain_param = Parameter.create(name='Gain', type='float', value=a.asserv.gain, step= 100)
		self.sampling_rate_param = Parameter.create(name='Sampling rate', type='int', value=a.asserv.sampling_rate, step= 100000, siPrefix=True, suffix='Samp/s')
		self.freq_mod_param = Parameter.create(name='Mod frequency', type='float', value=a.asserv.freq_mod, step= 1, siPrefix=True, suffix='Hz')
		self.cycle_number_param = Parameter.create(name='N cycle', type='int', value=a.asserv.cycle_number, step=1)
		self.discarded_samples_factor_param = Parameter.create(name='Ratio discarded samp.', type='float', value= a.asserv.discarded_samples_factor, step=0.05)
		self.n_samp_per_cycle_param = Parameter.create(name='N samp/cycle', type='int', value=a.asserv.n_samp_per_cycle, readonly=True)
		self.act_freq_mod_param = Parameter.create(name='Actual Mod frequency', type='float', value=a.asserv.freq_mod, siPrefix=True, suffix='Hz', readonly=True)
		self.update_interval_param = Parameter.create(name='Update interval', type='float', value=a.asserv.update_interval, siPrefix=True, suffix='s', readonly=True)
		gp6.addChildren([self.cpt_lock_param,self.gain_param,self.sampling_rate_param,self.freq_mod_param,self.cycle_number_param,self.discarded_samples_factor_param,self.act_freq_mod_param, self.n_samp_per_cycle_param, self.update_interval_param])

		gp7 = pTypes.GroupParameter(name='Temperature controller')
		self.t_setpoint_param = Parameter.create(name='T setpoint', type='float', value=a.regulation.setpoint)
		self.p_gain_param = Parameter.create(name='P gain', type='float', value=a.regulation.p_gain)
		self.i_gain_param = Parameter.create(name='I gain', type='float', value=a.regulation.i_gain)
		self.d_gain_param = Parameter.create(name='D gain', type='float', value=a.regulation.d_gain)
		gp7.addChildren([self.t_setpoint_param,self.p_gain_param,self.i_gain_param,self.d_gain_param])

		gp8 = pTypes.GroupParameter(name='Data logger')
		self.clear_plot_action = Parameter.create(name='Clear plot', type='action')
		gp8.addChildren([self.clear_plot_action])

		gp9 = pTypes.GroupParameter(name='Laser freq scan')

		gp10 = pTypes.GroupParameter(name='Frequency scan')
		self.scan_sampling_rate_param = Parameter.create(name='Sampling rate', type='int', value=a.syncAiAo.sampling_rate, step= 100000, siPrefix=True, suffix='Samp/s')
		self.scan_sample_number = Parameter.create(name='Sample number', type='int', value=a.syncAiAo.numSamp, step= 1000)
		self.fit_action = Parameter.create(name='Fit', type='action')
		self.show_data_cruve = Parameter.create(name='Show data curve', type='bool', value=True)
		self.show_mean_cruve = Parameter.create(name='Show mean curve', type='bool', value=True)
		self.show_fit_cruve = Parameter.create(name='Show fitting curve', type='bool', value=True)
		gp10.addChildren([self.scan_sampling_rate_param,self.scan_sample_number,self.fit_action,self.show_data_cruve, self.show_mean_cruve,self.show_fit_cruve])

		gp11 = pTypes.GroupParameter(name='Automated tasks')
		self.refresh_task_list_action = Parameter.create(name='Refresh list', type='action')
   		self.task_list = Parameter.create(name='Task',type='list', values= {"":None})
   		self.run_task_action = Parameter.create(name='Start', type='action')
   		self.stop_task_action = Parameter.create(name='Stop', type='action')
		gp11.addChildren([self.refresh_task_list_action,self.task_list,self.run_task_action,self.stop_task_action])

		gsp1.addChildren([gp1, gp2, gp3, gp4, gp5, gp6, gp7])
		params = [gp0,gsp1, gp8, gp9,gp10,gp11]

		self.p = Parameter.create(name='params', type='group', children=params)
		t = ParameterTree()
		t.setParameters(self.p, showTop=False)

		self.p.sigTreeStateChanged.connect(self.change)
		self.fs_freq_offset_action.sigActivated.connect(self.freq_jump)
		self.refresh_task_list_action.sigActivated.connect(self.on_refresh_task_list)
		self.run_task_action.sigActivated.connect(self.on_run_task)
		self.stop_task_action.sigActivated.connect(self.on_stop_task)
		self.clear_plot_action.sigActivated.connect(a.dl.empty)
		self.fit_action.sigActivated.connect(self.window.live_graph_widget.fit)

		self.addWidget(self.startLaserScanBtn,row=0, col=0)
		self.addWidget(self.startFreqScanBtn,row=1, col=0)
		self.addWidget(self.startAsservBtn,row=2, col=0)
		self.addWidget(self.startDlBtn,row=3, col=0)
		self.addWidget(t,row=4, col=0)

	def change(self,param,changes):
		for param, change, data in changes:
			if param is self.laserLockParam: a.lock_box.lock = param.value()
			elif param is self.laser_dc_offset_param: a.laserCtrl.dc_offset = param.value()
			elif param is self.laserLockInAmp: a.li_las.amplitude = param.value()
			elif param is self.laserLockInPhase: a.li_las.phase = param.value()
			elif param is self.laserLockInFreq:	a.li_las.ref_freq = param.value()
			elif param is self.fs_pow_amp_param: a.fs.power_amplitude = param.value()
			elif param is self.fs_fm_dev_param:
				a.fs.fm_dev = param.value()
				self.window.live_graph_widget.fm_dev = a.fs.fm_dev
			elif param is self.mag_cur_out_param: a.mag_cur_source.output = param.value()
			elif param is self.mag_cur_int_param: a.mag_cur_source.current_set_point = param.value()
			elif param is self.eom_dc_bias_param: a.biasCtrl.dc_bias = param.value()
			elif param is self.eom_dc_bias_lock_param:
				if param.value(): a.biasCtrl.start_canceller()
				else: a.biasCtrl.stop_canceller()
			elif param is self.canceller_p_gain_param: a.biasCtrl.canceller_p_gain = param.value()
			elif param is self.canceller_i_gain_param: a.biasCtrl.canceller_i_gain = param.value()
			elif param is self.opt_pow_param: a.powCtrl.power = param.value()
			elif param is self.nois_eat_param: a.powCtrl.noise_eater_voltage = param.value()
			elif param is self.pow_holder_param:
				if param.value(): a.powCtrl.holdPower()
				else: a.powCtrl.stopHolder()
			elif param is self.pow_holder_method_param: a.powCtrl.selected_holder_method = param.value()
			elif param is self.holder_p_gain_param: a.powCtrl.holder_p_gain = param.value()
			elif param is self.holder_i_gain_param: a.powCtrl.holder_i_gain = param.value()
			elif param is self.cpt_lock_param: a.asserv.lock = param.value()
			elif param is self.gain_param: a.asserv.gain = param.value()
			elif param is self.fs_freq_param:
				a.fs.frequency = param.value()
				self.par.live_graph_widget.update_label()
			elif param is self.sampling_rate_param:
				a.asserv.sampling_rate = param.value()
				self.update_readonly_params()
			elif param is self.freq_mod_param: 
				a.asserv.freq_mod = param.value()
				self.update_readonly_params()
			elif param is self.cycle_number_param:
				a.asserv.cycle_number = param.value()
				self.update_readonly_params()
			elif param is self.discarded_samples_factor_param: a.asserv.discarded_samples_factor = param.value()
			elif param is self.scan_sampling_rate_param: a.syncAiAo.sampling_rate = param.value()
			elif param is self.scan_sample_number: a.syncAiAo.numSamp = param.value()
			elif param is self.show_data_cruve: self.window.live_graph_widget.curve.setVisible(param.value())
			elif param is self.show_mean_cruve: self.window.live_graph_widget.meanCurve.setVisible(param.value())
			elif param is self.show_fit_cruve: self.window.live_graph_widget.fitCurve.setVisible(param.value())
			elif param is self.t_setpoint_param: a.regulation.setpoint = param.value()
			elif param is self.p_gain_param: a.regulation.p_gain = param.value()
			elif param is self.i_gain_param: a.regulation.i_gain = param.value()
			elif param is self.d_gain_param: a.regulation.d_gain = param.value()

	def update_readonly_params(self):
		self.act_freq_mod_param.setValue(a.asserv.freq_mod)
		self.n_samp_per_cycle_param.setValue(a.asserv.n_samp_per_cycle)
		self.update_interval_param.setValue(a.asserv.update_interval)

	def on_startLaserScanBtn(self):
		if self.startLaserScanBtn.isChecked():
			a.laserSyncAiAo.start()
			self.window.abs_graph_widget.start_timer()
			self.startLaserScanBtn.setText("Stop Laser Scan")
		else:
			a.laserSyncAiAo.stop()
			self.window.abs_graph_widget.stop_timer()
			self.startLaserScanBtn.setText("Start Laser Scan")

	def on_startFreqScanBtn(self):
		if self.startFreqScanBtn.isChecked():
			a.syncAiAo.start()
			self.window.live_graph_widget.start_timer()
			self.startFreqScanBtn.setText("Stop Frequency Scan")
		else:
			a.syncAiAo.stop()
			self.window.live_graph_widget.stop_timer()
			self.startFreqScanBtn.setText("Start Frequency Scan")

	def on_startAsservBtn(self):
		if self.startAsservBtn.isChecked():
			a.asserv.start()
			self.startAsservBtn.setText("Stop Asserv")
		else:
			a.asserv.stop()
			self.startAsservBtn.setText("Start Asserv")

	def on_startDlBtn(self):
		if self.startDlBtn.isChecked():
			a.dl.start()
			self.startDlBtn.setText("Stop Data Logging")
		else:
			a.dl.stop()
			self.startDlBtn.setText("Start Data Logging")

	def freq_jump(self):
		a.fs.frequency = a.fs.frequency + self.fs_freq_offset_value.value()

	# def on_set_opt_pow(self):
	# 	powCtrl.power = self.opt_pow_param.value()

	def on_refresh_task_list(self):
		reload(tasks.automation)
		dic = {}
		for name, obj in inspect.getmembers(tasks.automation):
			if inspect.isclass(obj):
				print name, obj
				dic.update({name:obj})
		self.task_list.setLimits(dic)

	def on_run_task(self):
		if self.task:
			self.task.stop()
		selectedTaskClass = self.task_list.value()
		self.task = selectedTaskClass(a,self.window)
		self.task.start()

	def on_stop_task(self):
		if self.task:
			self.task.stop()		

class DataGraphWidget(pg.GraphicsLayoutWidget):
	def __init__(self, window=None):
		super(DataGraphWidget, self).__init__(window)

		def addLabelPlot(pen="w",label1=" ",label2=" ",xlinkp=None,hideXAxis=True):
			self.addLabel(label1, col=0)
			l2 = self.addLabel(label2, col=1)
			self.nextRow()
			p = self.addPlot(colspan=2)
			c = p.plot(pen = pen)
			if xlinkp: p.setXLink(xlinkp)
			p.setDownsampling(mode='peak')
			p.setClipToView(True)
			p.showGrid(x=True, y=True, alpha=1)
			if hideXAxis:
				p.hideAxis('bottom')
			self.nextRow()
			return p, c, l2

		p1, self.c1, self.c1_label  = addLabelPlot('m',"Frequency (Hz)")
		p2, self.c2, _  = addLabelPlot('c',"Error") #,xlinkp=p1)
		p3, self.c3, _  = addLabelPlot('r',"Mean signal (V)") #,xlinkp=p1)
		p4, self.c4, _  = addLabelPlot('g',"Heater current (A)") #,xlinkp=p1)
		p5, self.c5, _  = addLabelPlot('w',"Cell temperature (degC)") #,xlinkp=p1)
		p6, self.c6, _  = addLabelPlot('y',"Power meter (uW)") #,xlinkp=p1)
		p7, self.c7, _  = addLabelPlot('c',"Ext temperature (degC)") #,xlinkp=p1)
		p8, self.c8, _  = addLabelPlot('r',"Noise eater DC (V)") #,xlinkp=p1)
		p9, self.c9, _  = addLabelPlot('g',"Carrier signal (V)") #,xlinkp=p1)
		p10, self.c10, _  = addLabelPlot('w',"EOM DC bias (V)",hideXAxis=False) #,xlinkp=p1)

		self.timer = QtCore.QTimer()
		self.timer.timeout.connect(self.update1)
		self.timer.start(500)

		self.timer2 = QtCore.QTimer()
		self.timer2.timeout.connect(self.update2)
		self.timer2.start(1000)

		self.timer3 = QtCore.QTimer()
		self.timer3.timeout.connect(self.update3)
		self.timer3.start(100)


	def update(self):
		self.update1()
		self.update2()

	def update1(self):
		if a.dl.asservConsThread and  a.dl.asservConsThread.data.ptr -1 > 2:
			currentDataPtr = a.dl.asservConsThread.data.ptr -1
			pcTimes = a.dl.asservConsThread.data.array[0:currentDataPtr,0]
			self.c1.setData(x=pcTimes, y=a.dl.asservConsThread.data.array[0:currentDataPtr,3])
			self.c2.setData(x=pcTimes, y=a.dl.asservConsThread.data.array[0:currentDataPtr,4])
			self.c3.setData(x=pcTimes, y=a.dl.asservConsThread.data.array[0:currentDataPtr,5])

	def update2(self):
		if  a.dl.consThread and a.dl.consThread.data.ptr - 1 > 2:
			currentDataPtr = a.dl.consThread.data.ptr - 1
			pcTimes = a.dl.consThread.data.array[0:currentDataPtr,0]
			self.c4.setData(x=pcTimes, y=a.dl.consThread.data.array[0:currentDataPtr,5])
			self.c5.setData(x=pcTimes, y=a.dl.consThread.data.array[0:currentDataPtr,2])
			self.c6.setData(x=pcTimes, y=a.dl.consThread.data.array[0:currentDataPtr,1])
			self.c7.setData(x=pcTimes, y=a.dl.consThread.data.array[0:currentDataPtr,3])
			self.c8.setData(x=pcTimes, y=a.dl.consThread.data.array[0:currentDataPtr,4])
			self.c9.setData(x=pcTimes, y=a.dl.consThread.data.array[0:currentDataPtr,6])
			self.c10.setData(x=pcTimes, y=a.dl.consThread.data.array[0:currentDataPtr,7])

	def update3(self):
		if a.dl.asservConsThread and  a.dl.asservConsThread.data.ptr -1 > 2:
			currentDataPtr = a.dl.asservConsThread.data.ptr -1
			mean = np.mean(a.dl.asservConsThread.data.array[0:currentDataPtr,2])
			std_dev = np.std(a.dl.asservConsThread.data.array[0:currentDataPtr,3])
			self.c1_label.setText("Mean: {:.3f} Hz   Std dev: {:.3f} Hz".format(mean,std_dev))

class LiveGraphWidget(pg.GraphicsLayoutWidget):
	def __init__(self, window=None):
		super(LiveGraphWidget, self).__init__(window)
		labelStyle = {'color': '#FFF', 'size': '10pt'}
		self.meas_lbl = self.addLabel("Measurements",**labelStyle)
		self.nextRow()
		self.p = self.addPlot()
		self.p.showGrid(x=True, y=True, alpha=0.8)
		self.curve = self.p.plot(pen=pg.mkPen((0, 255, 255,60)))
		self.meanCurve = self.p.plot(pen=pg.mkPen((0, 255, 255,255)))
		self.fitCurve = self.p.plot(pen="r")
		self.timer = QtCore.QTimer()
		self.timer.timeout.connect(self.update)
		self.fm_dev = None
		self.p.setLabel('left', "Signal", units='V')
		self.p.setLabel('bottom', "FM modulation signal", units='V')

	def update(self):
		x, y = a.syncAiAo.getNthChanAIdata(0)
		_, y2 = a.syncAiAo.getNthChanAImean(0)
		if self.fm_dev:
			x = x*self.fm_dev
		background = np.min(y2)
		signal = np.max(y2)-background
		contrast = signal/background
		self.meas_lbl.setText("Signal: {:.4f} mV    Background: {:.4f} mV  Contrast: {:.2f} %".format(signal*1000,background*1000,contrast*100))
		self.curve.setData(x=x,y=y)
		self.meanCurve.setData(x=x,y=y2)
		if a.syncAiAo.counter == 1:
			self.p.enableAutoRange('xy', False)

	def update_label(self):
		self.frequency = a.fs.frequency
		self.p.setLabel('bottom', "Frequency shift from {:.2f}".format(self.frequency), units='Hz')

	def start_timer(self):
		self.fm_dev = a.fs.fm_dev
		self.update_label()
		self.timer.start(50)

	def stop_timer(self):
		self.timer.stop()

	def fit(self):
		x, y = a.syncAiAo.getNthChanAImean(0)
		if self.fm_dev:
			x = x*self.fm_dev
		self.fitter = Fitter(x,y)
		self.fitter.newData.connect(self.update_fit_curve)
		self.fitter.start()

	def update_fit_curve(self,x,fitData):
		self.fitCurve.setData(x=x,y=fitData)


class AbsGraphWidget(pg.GraphicsLayoutWidget):
	def __init__(self, window=None):
		super(AbsGraphWidget, self).__init__(window)
		self.p = self.addPlot()
		self.p.showGrid(x=True, y=True, alpha=0.8)
		self.signalCurve = self.p.plot(pen="m")
		self.errorCurve = self.p.plot(pen="c")
		self.timer = QtCore.QTimer()
		self.timer.timeout.connect(self.update)
		self.p.setLabel('left', "Signal", units='V')
		self.p.setLabel('bottom', "Laser modulation signal", units='V')	

	def update(self):
		x, y = a.laserSyncAiAo.getNthChanAIdata(0)
		_, y2 = a.laserSyncAiAo.getNthChanAImean(1)
		self.signalCurve.setData(x=x,y=y)
		self.errorCurve.setData(x=x,y=y2)
		if a.laserSyncAiAo.counter == 1:
			self.p.enableAutoRange('xy', False)

	def start_timer(self):
		self.timer.start(50)

	def stop_timer(self):
		self.timer.stop()

class MyWindow(QtGui.QMainWindow):
	def __init__(self):
		QtGui.QMainWindow.__init__(self)
		self.setWindowTitle("qtMain")
		self.resize(1400,900)

		self.data_graph_widget = DataGraphWidget(self)
		self.live_graph_widget = LiveGraphWidget(self)
		self.abs_graph_widget = AbsGraphWidget(self)
		self.control_widget = ControlWidget(self)

		area = DockArea()
		self.setCentralWidget(area)
		d1 = Dock("Controls", size=(400, 1))
		d2 = Dock("Data logger", size=(1000, 1))
		d3 = Dock("CPT signal", size=(1000, 1))
		d4 = Dock("Abs. signal", size=(1000, 1))
		
		area.addDock(d1, 'left')
		area.addDock(d2, 'right')
		area.addDock(d3, 'above', d2)
		area.addDock(d4, 'above', d3)
		d1.addWidget(self.control_widget)
		d2.addWidget(self.data_graph_widget)
		d3.addWidget(self.live_graph_widget)
		d4.addWidget(self.abs_graph_widget)

a = DeviceSet()	
a.dl = DataLogger()

app = QtGui.QApplication([])
win = MyWindow()
win.show()

if __name__ == "__main__":
	if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
		ret = QtGui.QApplication.instance().exec_()
		sys.exit(ret)