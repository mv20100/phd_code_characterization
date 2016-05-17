# import threading
import numpy as np
import pyqtgraph as pg
import time
from utils.fitting import fitPolynomial, polyFitFunc

log_separator = ","
data_folder_path = "G:\eric.kroemer\Desktop\Vincent\Pilotage Data"

class TemperatureScanWorker(pg.QtCore.QThread):

	newData = pg.QtCore.Signal(object)
	pow_scan_complete = pg.QtCore.Signal(object)
	running = False

	def __init__(self, task):
		pg.QtCore.QThread.__init__(self)
		self.task = task

	def stop(self):
		self.running = False

	def run(self):
		ds = self.task.ds
		assert not self.running
		self.running = True
		print("Automated task running")
		temperatures = np.arange(50,85)[::-1]
		powers = [10.,20.,30.,40.,50.]
		for temperature in temperatures:
			ds.regulation.setpoint = temperature
			for power in powers:
				ds.powCtrl.setPower(power)
				ds.dl.empty()
				print("Waiting for measurement")
				while self.running:
					if ds.dl.asservConsThread.is_full():
						pow_data = ds.dl.consThread.data.get_data()[:,1]
						temp_data = ds.dl.consThread.data.get_data()[:,2]
						heat_cur_data = ds.dl.consThread.data.get_data()[:,5]
						pow_stdev = np.std(pow_data)
						temp_stdev = np.std(temp_data)
						if pow_stdev < 0.05 and temp_stdev < 0.05:
							pow_mean = np.mean(pow_data)
							break
					time.sleep(5)
				if not self.running: return
				freq_mean = np.mean(ds.dl.asservConsThread.data.get_data()[:,2])
				print("Measurement done: {} Hz {} uW".format(freq_mean, pow_mean))
				self.newData.emit([pow_mean,freq_mean])

			self.pow_scan_complete.emit([np.mean(temp_data),np.mean(heat_cur_data)])
		print("Automated task done")
		self.running = False

class TemperatureScan(object):

	def __init__(self, deviceSet, window):
		self.ds = deviceSet
		self.window = window
		self.worker = TemperatureScanWorker(self)
		self.gw = pg.GraphicsWindow()
		self.p = self.gw.addPlot()
		self.curve = self.p.plot(pen="w",symbol='o')
		self.fit = self.p.plot(pen="r")
		self.p.setLabel('left', "Frequency", units='Hz')
		self.p.setLabel('bottom', "Input optical power", units='uW')
		
		self.gw.nextRow()

		self.p2 = self.gw.addPlot()
		self.curve2 = self.p2.plot(pen="w",symbol='o',symbolBrush='r')
		self.p2.setLabel('left', "Null power frequency", units='Hz')
		self.p2.setLabel('bottom', "Temperature", units='degC')

		self.gw.nextRow()

		self.p3 = self.gw.addPlot()
		self.curve3 = self.p3.plot(pen="w",symbol='o',symbolBrush='r')
		self.p3.setLabel('left', "Heater current", units='A')
		self.p3.setLabel('bottom', "Temperature", units='degC')

	def start(self):
		self.worker.newData.connect(self.update)
		self.worker.pow_scan_complete.connect(self.updateTemp)
		self.nullPowerFreqs = []
		self.temperatures = []
		self.heater_currents = []
		self.powers = []
		self.frequencies = []
		self.worker.start()

	def stop(self):
		if self.worker.running:
			self.worker.running = False
			self.worker.wait()
			print "Task stopped"
		else:
			print "Task not running"

	def update(self,data):
		self.powers.append(data[0])
		self.frequencies.append(data[1])
		self.curve.setData(x=self.powers,y=self.frequencies)

	def updateTemp(self,data):
		temp = data[0]
		heater_current = data[1]
		out = fitPolynomial(self.powers, self.frequencies, 2)
		x, y = polyFitFunc(out, 0, max(self.powers),30)
		self.powers = []
		self.frequencies = []
		self.fit.setData(x=x,y=y)
		self.curve = self.p.plot(pen="w",symbol='o')
		self.fit = self.p.plot(pen="r")
		self.nullPowerFreqs.append(out.best_values['c0'])
		self.temperatures.append(temp)
		self.heater_currents.append(heater_current)
		self.curve2.setData(x=self.temperatures,y=self.nullPowerFreqs)
		self.curve3.setData(x=self.temperatures,y=self.heater_currents)

class ImagRangeTaskWorker(pg.QtCore.QThread):

	newData = pg.QtCore.Signal(object)
	pow_scan_complete = pg.QtCore.Signal(object)
	running = False

	def __init__(self, task):
		pg.QtCore.QThread.__init__(self)
		self.task = task

	def stop(self):
		self.running = False

	def run(self):
		ds = self.task.ds
		assert not self.running
		self.running = True
		print("Automated task running")
		mag_currents = np.linspace(0.5,50,50)
		powers = [10.,20.,30.,40.,50.]
		for mag_current in mag_currents:
			ds.mag_cur_source.current_set_point = mag_current
			for power in powers:
				ds.powCtrl.setPower(power)
				ds.dl.empty()
				print("Waiting for measurement")
				while self.running:
					if ds.dl.asservConsThread.is_full():
						pow_data = ds.dl.consThread.data.get_data()[:,1]
						pow_stdev = np.std(pow_data)
						if pow_stdev < 0.05:
							pow_mean = np.mean(pow_data)
							break
					time.sleep(5)
				if not self.running: return
				freq_mean = np.mean(ds.dl.asservConsThread.data.get_data()[:,2])
				print("Measurement done: {} Hz {} uW".format(freq_mean, pow_mean))
				self.newData.emit([pow_mean,freq_mean])

			self.pow_scan_complete.emit([mag_current])
		print("Automated task done")
		self.running = False

class ImagRangeTask(object):

	def __init__(self, deviceSet, window):
		self.ds = deviceSet
		self.win = window
		self.worker = ImagRangeTaskWorker(self)
		self.gw = pg.GraphicsWindow()
		self.p = self.gw.addPlot()
		self.curve = self.p.plot(pen="w",symbol='o')
		self.fit = self.p.plot(pen="r")
		self.p.setLabel('left', "Frequency", units='Hz')
		self.p.setLabel('bottom', "Input optical power", units='uW')
		
		self.gw.nextRow()

		self.p2 = self.gw.addPlot()
		self.curve2 = self.p2.plot(pen="w",symbol='o',symbolBrush='r')
		self.p2.setLabel('left', "Null power frequency", units='Hz')
		self.p2.setLabel('bottom', "Coil current", units='mA')

	def start(self):
		self.worker.newData.connect(self.update)
		self.worker.pow_scan_complete.connect(self.update2)
		self.nullPowerFreqs = []
		self.mag_currents = []
		self.powers = []
		self.frequencies = []
		self.worker.start()

	def stop(self):
		if self.worker.running:
			self.worker.running = False
			self.worker.wait()
			print "Task stopped"
		else:
			print "Task not running"

	def update(self,data):
		self.powers.append(data[0])
		self.frequencies.append(data[1])
		self.curve.setData(x=self.powers,y=self.frequencies)

	def update2(self,data):
		mag_current = data[0]
		out = fitPolynomial(self.powers, self.frequencies, 2)
		x, y = polyFitFunc(out, 0, max(self.powers),30)
		self.powers = []
		self.frequencies = []
		self.fit.setData(x=x,y=y)
		self.curve = self.p.plot(pen="w",symbol='o')
		self.fit = self.p.plot(pen="r")

		self.nullPowerFreqs.append(out.best_values['c0'])
		self.mag_currents.append(mag_current)
		self.curve2.setData(x=self.mag_currents,y=self.nullPowerFreqs)

class AgingAnalysisWorker(pg.QtCore.QThread):

	newData = pg.QtCore.Signal(object)
	pow_scan_complete = pg.QtCore.Signal(object)
	running = False

	def __init__(self, task):
		pg.QtCore.QThread.__init__(self)
		self.task = task

	def stop(self):
		self.running = False

	def run(self):
		ds = self.task.ds
		assert not self.running
		self.running = True
		print("Automated task running")
		powers = [10.,20.,30.,40.,50.]

		while self.running:
			for power in powers:
				ds.powCtrl.setPower(power)
				ds.dl.empty()
				print("Waiting for measurement")
				while self.running:
					if ds.dl.asservConsThread.is_full():
						pow_data = ds.dl.consThread.data.get_data()[:,1]
						pow_stdev = np.std(pow_data)
						if pow_stdev < 0.05:
							pow_mean = np.mean(pow_data)
							break
					time.sleep(5)
				if not self.running: return
				freq_mean = np.mean(ds.dl.asservConsThread.data.get_data()[:,2])
				print("Measurement done: {} Hz {} uW".format(freq_mean, pow_mean))
				self.newData.emit([pow_mean,freq_mean])

			self.pow_scan_complete.emit([time.time()])
		print("Automated task done")
		self.running = False

class AgingAnalysis(object):

	def __init__(self, deviceSet, window):
		self.ds = deviceSet
		self.window = window
		self.worker = AgingAnalysisWorker(self)
		self.gw = pg.GraphicsWindow()
		self.p = self.gw.addPlot()
		self.curve = self.p.plot(pen="w",symbol='o')
		self.fit = self.p.plot(pen="r")
		self.p.setLabel('left', "Frequency", units='Hz')
		self.p.setLabel('bottom', "Input optical power", units='uW')
		
		self.gw.nextRow()

		self.p2 = self.gw.addPlot()
		self.curve2 = self.p2.plot(pen="w",symbol='o',symbolBrush='r')
		self.p2.setLabel('left', "Null power frequency", units='Hz')
		self.p2.setLabel('bottom', "Time")

	def start(self):
		timeStr = time.strftime("%Y-%m-%d %H%M")
		cellname = self.window.control_widget.cellName.value()
		self.file = open("{}\\aging {} {}.txt".format(data_folder_path,cellname,timeStr),'a')

		self.worker.newData.connect(self.update)
		self.worker.pow_scan_complete.connect(self.update2)
		self.nullPowerFreqs = []
		self.times = []
		self.powers = []
		self.frequencies = []
		self.worker.start()

	def stop(self):
		if self.worker.running:
			self.worker.running = False
			self.worker.wait()
			self.file.close()
			print "Task stopped"
		else:
			print "Task not running"

	def update(self,data):
		self.powers.append(data[0])
		self.frequencies.append(data[1])
		self.curve.setData(x=self.powers,y=self.frequencies)

	def update2(self,data):
		ttime = data[0]
		out = fitPolynomial(self.powers, self.frequencies, 2)
		x, y = polyFitFunc(out, 0, max(self.powers),30)
		data = [str(ttime),';'.join(["%.6f"%(item) for item in self.powers]),';'.join(["%.6f"%(item) for item in self.frequencies]),str(out.best_values['c0']),str(out.best_values['c1']),str(out.best_values['c2'])]
		self.file.write(log_separator.join(data)+"\n")
		self.powers = []
		self.frequencies = []
		self.fit.setData(x=x,y=y)
		# self.curve = self.p.plot(pen="w",symbol='o')
		# self.fit = self.p.plot(pen="r")
		self.nullPowerFreqs.append(out.best_values['c0'])
		self.times.append(ttime)
		self.curve2.setData(x=self.times,y=self.nullPowerFreqs)