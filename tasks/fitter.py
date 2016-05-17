import pyqtgraph as pg
import numpy as np
from utils.fitting import *


class Fitter(pg.QtCore.QThread):

	newData = pg.QtCore.Signal(object,object)

	def __init__(self,x,y):
		pg.QtCore.QThread.__init__(self)
		self.x = x
		self.y = y

	def run(self):
		init, fitOut = fitLorentzian(self.x,self.y)
		self.newData.emit(self.x,fitOut.best_fit)
