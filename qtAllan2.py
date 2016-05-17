from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg
from pyqtgraph.dockarea import *
import pyqtgraph.parametertree.parameterTypes as pTypes
from pyqtgraph.parametertree import Parameter, ParameterTree, ParameterItem, registerParameterType
import numpy as np
import time, allantools, sys, os

data_folder_path = "G:\eric.kroemer\Desktop\Vincent\Pilotage Data"
log_separator = ","
header_lines = 1
time_col_header = 'Time'
default_hidden_columns = ["DAQ time (s)","Error","Correction (Hz)","Heater current (A)","Carrier signal (V)","Laser current modulation signal (V)"]

def readHeader(filename):
    logfile = open(filename,"r")
    line = logfile.readline()
    header = line[:-1].split(log_separator)
    return header

def readLines(filename,read_every=1):
    lines = []
    logfile = open(filename,"r")
    line_number = 0
    # loglines = follow(logfile)
    while True:
        line = logfile.readline()
        if line:
            line_number += 1
            if line_number % read_every == 0:
                lines.append(line[:-1].split(log_separator))
            if line_number % 1000 == 0:
                sys.stdout.write("\rReading file: {} lines read".format(line_number))
                sys.stdout.flush()
        else:
            break
    sys.stdout.write("\r{} lines read, {} lines kept\n".format(line_number,len(lines)))
    return lines[0], lines[header_lines:-1]

def open_filename():
    filenames = QtGui.QFileDialog.getOpenFileNames(None, 'Select datalog file', data_folder_path, selectedFilter='*.txt')
    return filenames

class ColumnData(object):

    def __init__(self,parent,header,index):
        self.parent = parent
        self.header = header
        self.index = index
        self.time_data = False
        self.plot = None
        self.curve = None
        if self.header == time_col_header:
            self.time_data = True

class FileData(object):
    
    def __init__(self,parent=None,filename=None):
        
        self.parent = parent
        self.fullfilename = filename
        self.basename = os.path.basename(str(self.fullfilename))
        self.headers = readHeader(self.fullfilename)
        # self.load_data()
        self.basep = Parameter.create(name=self.basename, type='group')
        self.read_subsamp_param = Parameter.create(name='Read subsampling', type='int', value=1)
        self.subsampling_param = Parameter.create(name='Plot subsampling', type='int', value=10)
        self.basep.addChildren([self.read_subsamp_param,self.subsampling_param])
        self.active_read_subsamp = None
        self.active_subsampling = None
        self.last_file_size = None
        
        self.children = []
        for idx, header in enumerate(self.headers):
            columnData = ColumnData(self,header,idx)
            self.children.append(columnData)

    def file_changed(self):
        file_size = os.stat(self.fullfilename).st_size
        if self.last_file_size and self.last_file_size == file_size:
            return False
        self.last_file_size = file_size
        return True

    def load_data(self):
        if self.file_changed() or (self.active_read_subsamp and self.active_read_subsamp != self.read_subsamp_param.value()):
            self.active_read_subsamp = self.read_subsamp_param.value()
            _ , self.array = readLines(self.fullfilename,read_every=self.active_read_subsamp)
            print "Preparing array"
            self.np_array = np.array(self.array,dtype=float)
            self.make_sub_array()
        else:
            if self.active_subsampling != self.subsampling_param.value():
                self.make_sub_array()

    def make_sub_array(self):
        print "Preparing subsampled array"
        self.active_subsampling = self.subsampling_param.value()
        self.sub_np_array = self.np_array[0::self.active_subsampling,:]

    @property
    def subsampling(self):
        return self.subsampling_param.value



class TimeAxisItem(pg.AxisItem):
    def __init__(self, *args, **kwargs):
        super(TimeAxisItem,self).__init__(*args, **kwargs)

    def tickStrings(self, values, scale, spacing):
        return [time.strftime("%H:%M:%S\n%d-%m", time.localtime(value)) for value in values]


class LongValueAxisItem(pg.AxisItem):
    def __init__(self, *args, **kwargs):
        super(LongValueAxisItem,self).__init__(*args, **kwargs)

    def tickStrings(self, values, scale, spacing):
        return ["{:.12g}".format(value) for value in values]


class MyWindow(QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)

        self.filedatas = []
        area = DockArea()
        self.setCentralWidget(area)
        self.setWindowTitle('Allan')
        self.resize(1800,900)
        d1 = Dock("Controls", size=(300, 1))
        d2 = Dock("Graphs", size=(900, 1))
        d3 = Dock("Allan dev", size=(600, 1))
        area.addDock(d1, 'left')
        area.addDock(d2, 'right')
        area.addDock(d3, 'right')

        pg.setConfigOptions(antialias=True)

        add_file_action = Parameter.create(name='Add files', type='action')
        remove_files_action = Parameter.create(name='Remove files', type='action')
        self.file_group = Parameter.create(name='Files', type='group')
        self.columns_group = Parameter.create(name='Columns', type='group')
        plot_action = Parameter.create(name='Plot', type='action')
        reload_action = Parameter.create(name='Reload and plot', type='action')
        self.link_x_views_param = Parameter.create(name='Link x axis', type='bool', value=True)
        allan_group = Parameter.create(name='Allan Dev', type='group')
        self.allan_var_param = Parameter.create(name='Variable',type='list', values= {"":None})
        self.fractional_var_param = Parameter.create(name='Fractionalize',type='bool',value=True)
        update_allan_action = Parameter.create(name='Update Allan Dev', type='action')
        allan_group.addChildren([self.allan_var_param,self.fractional_var_param,update_allan_action])

        params = [add_file_action,remove_files_action,self.file_group,self.columns_group,plot_action,reload_action,self.link_x_views_param,allan_group]
        self.base_param = Parameter.create(name='params', type='group', children=params)
        self.param_tree = ParameterTree()
        self.param_tree.setParameters(self.base_param, showTop=False)
        d1.addWidget(self.param_tree)
        
        self.base_param.sigTreeStateChanged.connect(self.change)
        add_file_action.sigActivated.connect(self.add_file)
        remove_files_action.sigActivated.connect(self.remove_files)
        reload_action.sigActivated.connect(self.reload_data)
        plot_action.sigActivated.connect(self.plot)
        update_allan_action.sigActivated.connect(self.updateAllan)

        # Time graphs
        self.plots_layout = pg.GraphicsLayoutWidget() # border=(100,100,100)
        self.plots = []
        d2.addWidget(self.plots_layout)

        # Allan dev graph
        l2 = pg.GraphicsLayoutWidget() # border=(100,100,100)
        d3.addWidget(l2)


        self.pa = l2.addPlot(title="Stability")
        self.pa.setLabel('left', "Allan deviation")
        self.pa.setLabel('bottom', "Integration time", units='s')
        self.curvea = self.pa.plot(pen="g")
        self.err_bara = pg.ErrorBarItem(x=0,y=0,beam=0.05,pen=pg.mkPen(0,255,0,100))
        self.pa.setLogMode(x=True, y=True)
        self.pa.addItem(self.err_bara)
        self.pa.showGrid(x=True, y=True, alpha=1)

        self.show()

    def change(self,param,changes):
        for param, change, data in changes:
            if param is self.link_x_views_param:
                if self.link_x_views_param.value(): self.link_plots_x_axis(True)
                else: self.link_plots_x_axis(False)

    def file_already_opened(self, filename):
        for fd in self.filedatas:
            if fd.fullfilename == filename:
                return True
        return False

    def add_file(self):
        filenames = open_filename()
        for filename in filenames:
            if not self.file_already_opened(filename):
                fd = FileData(self,filename)
                self.filedatas.append(fd)
                self.file_group.addChild(fd.basep)
        self.update_column_list()

    def find_column_param(self,header):
        for header_param in self.columns_group.children():
            if header_param.name() == header:
                return header_param
        return None

    def update_column_list(self):
        all_headers = []
        for fd in self.filedatas:
            for cd in fd.children:
                if not cd.time_data:
                    all_headers.append(cd.header)
        all_headers = list(set(all_headers))
        self.columns_group.clearChildren()
        for header in all_headers:
            value = header not in default_hidden_columns
            param = Parameter.create(name=header, type='bool', value=value)
            self.columns_group.addChild(param) 

    def remove_files(self):
        self.file_group.clearChildren()
        self.filedatas = []

    def reload_data(self):
        for fd in self.filedatas:
            fd.load_data()
        self.plot()

    def find_plot(self, columnName):
        for item in self.plots:
            if item['columnName'] == columnName:
                return item['plot']
        return None

    def clear_plots(self):
        for item in self.plots:
            plot = item['plot']
            plot.clear()

    def remove_empty_plots(self):
        for item in self.plots:
            plot = item['plot']
            if len(plot.listDataItems())==0:
                self.plots_layout.removeItem(plot)
                self.plots.remove(item)
    
    def get_plot_list(self):
        return [item['plot'] for item in self.plots]    

    def link_plots_x_axis(self,link=True):
        plot_list = self.get_plot_list()
        if len(plot_list)>1:
            plot_list[0].setXLink(None)
            for plot in plot_list[1:]:
                if link: plot.setXLink(plot_list[0])
                else: plot.setXLink(None)

    def plot(self):
        columnsList = []
        self.clear_plots()

        for fd in self.filedatas:
            fd.make_sub_array()
            for columnData in fd.children:
                param = self.find_column_param(columnData.header)
                if columnData.time_data or (param and param.value() == True):
                    columnData.data = fd.np_array[:,columnData.index]
                    columnData.sub_data = fd.sub_np_array[:,columnData.index]
                    if columnData.time_data:
                        fd.timeColumnData = columnData
                    else:
                        columnsList.append(columnData)
                        existing_plot = self.find_plot(columnData.header)
                        if existing_plot:
                            plot = existing_plot
                        else:
                            plot = self.plots_layout.addPlot(title=columnData.header,axisItems={'bottom': TimeAxisItem(orientation='bottom'), 'left': LongValueAxisItem(orientation='left')})
                            self.plots_layout.nextRow()
                            titleStyle = {'size': '9pt','align':'left'}
                            plot.setTitle(columnData.header,**titleStyle)
                            plot.showGrid(x=True, y=True, alpha=0.5)
                            plot.setDownsampling(mode='peak')
                            plot.setClipToView(True)
                            self.plots.append({"columnName":columnData.header,'plot':plot})
                        columnData.plot = plot
                        curve = plot.plot(pen="w")
                        curve.setData(x=fd.timeColumnData.sub_data,y=columnData.sub_data)
                        
        self.remove_empty_plots()
        
        self.link_plots_x_axis(True)

        plot_list = self.get_plot_list()
        if len(plot_list)>4:
            plot_list[-1].getAxis('bottom').setStyle(showValues=True)
            for plot in plot_list[0:-1]:
                plot.getAxis('bottom').setStyle(showValues=False)

        columnsDic = {}
        for column in columnsList:
            columnsDic.update({column.header:column})
        self.allan_var_param.setLimits(columnsDic)

    def updateAllan(self):

        # Get the selected column
        column = self.allan_var_param.value()
        data = column.data
        times = column.parent.timeColumnData.data
        # Check if DAQ must be used
        daq_times = None
        for sisterCol in column.parent.children:
            if "DAQ time" in sisterCol.header:
                sisterCol.data = column.parent.np_array[:,sisterCol.index]
                daq_times = sisterCol.data
        
        minTime, maxTime = column.plot.getViewBox().viewRange()[0]
        indexes = np.argwhere(np.logical_and(times >= minTime,times <= maxTime))
        if daq_times is not None:
            rate = 1./(daq_times[1] - daq_times[0])
        else: rate = len(times)/(max(times)-min(times))

        if self.fractional_var_param.value():
            data_freq = data[indexes]/data[indexes[0]]
        else:
            data_freq = data[indexes]

        taus = np.logspace(0.0,4.0,num=50)
        sys.stdout.write("Computing Allan deviation ")
        (tau_used, ad , ade, adn) =  allantools.adev(data_freq, rate, taus)
        sys.stdout.write("Done\n")
        x = tau_used
        y = ad
        top_error = np.log10(ad + ade/2) - np.log10(ad)
        bot_error = np.log10(ad) - np.log10(ad - ade/2)
        self.err_bara.setData(x=np.log10(x), y=np.log10(y), top=top_error, bottom=bot_error)
        self.curvea.setData(x=x,y=y)
        if self.fractional_var_param.value():
            self.pa.setTitle("Fractional - "+column.header)    
        else:
            self.pa.setTitle(column.header)



app = QtGui.QApplication([])
win = MyWindow()

if __name__=="__main__":

    import sys 
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        ret = QtGui.QApplication.instance().exec_()

        sys.exit(ret)