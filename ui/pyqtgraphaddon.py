import pyqtgraph.parametertree.parameterTypes as pTypes
from pyqtgraph.parametertree import Parameter, registerParameterType
from pyqtgraph import functions as fn
from pyqtgraph.widgets.SpinBox import SpinBox

class MySpinBox(SpinBox):
	def __init__(self, **opts):
		SpinBox.__init__(self, **opts)
	def updateText(self, prev=None):
		#print "Update text."
		self.skipValidate = True
		if self.opts['siPrefix']:
			if self.val == 0 and prev is not None:
				(s, p) = fn.siScale(prev)
				txt = "0.0 %s%s" % (p, self.opts['suffix'])
			else:
				txt = fn.siFormat(float(self.val), suffix=self.opts['suffix'])
		else:
			txt = '%.12g %s' % (self.val , self.opts['suffix'])
		self.lineEdit().setText(txt)
		self.lastText = txt
		self.skipValidate = False

class MyFloatParameterItem(pTypes.WidgetParameterItem):
	def __init__(self, param, depth):
		pTypes.WidgetParameterItem.__init__(self, param, depth)

	def makeWidget(self):
		opts = self.param.opts
		t = opts['type']
		
		if t == 'float2':
			defs = {
				'value': 0, 'min': None, 'max': None, 
				'step': 1.0, 'dec': False, 
				'siPrefix': False, 'suffix': ''
			}
			defs.update(opts)
			if 'limits' in opts:
				defs['bounds'] = opts['limits']
			w = MySpinBox(decimals=10)
			w.setOpts(**defs)
			w.sigChanged = w.sigValueChanged
			w.sigChanging = w.sigValueChanging
		else:
			raise Exception("Unknown type '%s'" % asUnicode(t))
		return w

class MyFloatParameter(Parameter):
	"""Editable string; displayed as large text box in the tree."""
	
	def __init__(self, **opts):
		Parameter.__init__(self, **opts)
		self.itemClass = MyFloatParameterItem

registerParameterType('float2', MyFloatParameter, override=True)
