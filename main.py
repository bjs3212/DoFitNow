# -*- coding: utf-8 -*-

RESOL = 10.0 ** (4) # 10 ** (N) 은 각 parameter에 N개의 소수점을 포함하겠다는 뜻
GRP_RESOL = 5000 # Fitting을 plot할때 resolution (point 개수)
Xrange_default = (0., 5000.) # X범위의 디폴트값
Yrange_default = (0., 1.) # Y범위의 디폴트값

from resources import Arrow_rc
import sys
import numpy as np
import pandas as pd
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QTableWidgetItem
from PyQt5.QtCore import pyqtSignal
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

def drude_sigma(w, wp, g) :
    return (wp*wp/(4*np.pi))*(1/(g-1j*w))

def local_drude_sigma(w, C, wp, g) :
    return drude_sigma(w, wp, g) * (1 + C*(1-(w*w/(g*g)))/(1+(w*w/(g*g))) )

# 메인 윈도우가 될 App 클래스
class App(QtWidgets.QMainWindow):
    # 추가할 것 : 메뉴 바, 각 윈도우(Fit, Plot, Model 등) 여는 버튼, 파일 업로드 기능
    def __init__(self):
        self.data_manager = DataManager() # 모든 데이터들을 중앙관리할 Data Manager 선언
        super().__init__()
        uic.loadUi('./ui/dfn.ui', self)
        self.modelButton = self.findChild(QtWidgets.QPushButton, 'modelButton')
        self.plotButton = self.findChild(QtWidgets.QPushButton, 'plotButton')
        self.uploadButton = self.findChild(QtWidgets.QPushButton, 'uploadButton')
        self.modelButton.clicked.connect(self.open_model_window)
        self.plotButton.clicked.connect(self.open_plot_window)
        self.uploadButton.clicked.connect(self.uploadDataFile)
        
        self.ParController = ParController(self, self.data_manager)

    def open_model_window(self):
        model_ = model(self, self.data_manager, modelname = 'M'+str(len(self.data_manager.models)+1))
        model_.show()
        model_.move(100,200*(len(self.data_manager.models)+1)) # 모델창 생성위치 조정
        
        self.ParController.show()
        self.ParController.move(600,200) # 파라미터 조절 슬라이더 생성위치 조절
    
    def open_plot_window(self):
        PlotWindow_ = PlotWindow(self, self.data_manager)
        PlotWindow_.show()
        
    def uploadDataFile(self):
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        fileName, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Open Data File", "", "All Files (*);;Text Files (*.txt)", options=options)
        if fileName: # 파일 타입에 따라 다르게 받는 것 구현 예정
            if 'csv' in fileName.split('/')[-1] : data = pd.read_csv(fileName, delimiter=',')
            else : data = pd.read_csv(fileName, delimiter=' ')
            # 첫 번째 열은 X축, 나머지 열은 Y축 데이터로 생각한다.
            data.name = fileName.split('/')[-1] # 파일 명을 data의 명으로
            data.dtype = 'S1' # 데이터 타입을 정할수 있게 하는 부분 추가예정
            self.data_manager.subscribe_data(data)
    
class DataManager(QtWidgets.QMainWindow) :
    tableClicked = pyqtSignal(float)
    sliderMoved = pyqtSignal(int)
    
    def __init__(self) :
        super().__init__()
        self.datas = []
        self.models = []
        self.plotWindows = []
        self.parControll = None
        
    def subscribe_data(self, data) :
        exist_dataNames = [data.name for data in self.datas]
        if data.name not in exist_dataNames:
            self.datas.append(data)
            
    def subscribe_model(self, model) :
        if model not in self.models:
            self.models.append(model)
            
    def subscribe_plot(self, plot_window) :
        if plot_window not in self.plotWindows:
            self.plotWindows.append(plot_window)
            
    def subscribe_parControll(self, parController) :
        self.parControll = parController
        
    def getdataNames(self) :
        return [dataset.name for dataset in self.datas]
    
    def getmodelNames(self) :
        return [model.name for model in self.models]
    
    def getmodelData(self, modelname, Xrange) :
        for model in self.models :
            if model.name == modelname :
                Xmin, Xmax = Xrange
                w = np.linspace(Xmin, Xmax, GRP_RESOL)
                modelData = np.zeros(w.shape)
                for oscillator in model.parameters :
                    C, wp, g = oscillator # oscillator 하나의 parameter 대입
                    modelData = modelData + local_drude_sigma(w, C, wp, g)
                return (w, modelData.real) # x축과 fit을 함께 return
                # 아직은 sigma의 real파트 계산만 만들어놓음
    
    def getData(self, dataname) :
        for dataset in self.datas :
            if dataset.name == dataname :
                keys = dataset.keys()
                w = dataset[keys[0]]
                datas = dataset[keys[1:]]
                return (w,datas) # x축과 data를 함께 return
    
    def parameter_changed(self, modelname, parameter, rowcolumn):
        row, column = rowcolumn
        for model in self.models :
            if model.name == modelname :
                model.parameters[row][column] = parameter
        self.update_plot(modelname)
        
    def update_plot(self, modelname) :
        for plotwindow in self.plotWindows :
            plotwindow.Canvas.update_plot(modelname)
    
    
    
# Fit에 필요한 변수들을 저장할 Table
class model(QtWidgets.QMainWindow):
    # 추후 추가할 것 : 테이블 행 추가, 각 행 별로 무슨 모델(lorentzian, drude 등) 쓸지 결정란 추가
    # Parameter (열) 도 모델에 따라서 추가되도록
    # 현재 모델이 여러개면 Slider로 각각 조절이 안되는 버그가 있음
    def __init__(self, main, data_manager, modelname):
        super().__init__(main)
        self.data_manager = data_manager
        self.data_manager.subscribe_model(self)
        uic.loadUi('./ui/model.ui', self)
        self.setWindowTitle(modelname)
        self.name = modelname
        self.table = self.findChild(QtWidgets.QTableWidget, 'ParTable')
        self.parameters = np.zeros((1,3), dtype=float) # each element is C, wp, Gamma
        self.initialize()
    
    def initialize(self):
        self.table.setItem(0,0, QTableWidgetItem(f"{self.parameters[0][0]:0.2f}"))
        self.table.setItem(0,1, QTableWidgetItem(f"{self.parameters[0][1]:0.2f}"))
        self.table.setItem(0,2, QTableWidgetItem(f"{self.parameters[0][2]:0.2f}"))
        
        self.table.cellClicked.connect(self.cell_clicked)
        self.table.cellChanged.connect(self.cell_changed)
        self.data_manager.sliderMoved.connect(self.update_cell_value)

    def cell_clicked(self, row, column):
        # 클릭된 셀의 값을 가져옵니다.
        value = self.parameters[row][column] if self.table.item(row, column) else None
        self.rowcolumn = (row,column)
        self.data_manager.tableClicked.emit(value)
        
    def cell_changed(self, row, column):
        parameter = float(self.table.item(row,column).text()) if self.table.item(row, column) else None
        self.data_manager.parameter_changed(self.name, parameter, (row, column))
        
    def update_cell_value(self, value):
        # 현재 선택된 셀의 값을 업데이트
        current_item = self.table.currentItem()
        if current_item:
            value = value/RESOL
            row, column = self.rowcolumn
            self.parameters[row][column]=value
            current_item.setText(str(f"{value:0.2f}"))
            
    
# 각 Parameter를 Slider형태로 조절하는 창    
class ParController(QtWidgets.QMainWindow):
    # 추가할 것 : Min Max 입력, 조절을 Linear로 할지 exponential하게 할지 선택?
    def __init__(self, main, data_manager):
        super().__init__(main)
        self.data_manager = data_manager
        self.data_manager.subscribe_parControll(self)
        uic.loadUi('./ui/ParController.ui', self)
        self.slider = self.findChild(QtWidgets.QSlider, 'ParController_Slider')
        self.slider.sliderMoved.connect(self.slider_moved)
        self.slider.sliderReleased.connect(self.on_slider_released)
        self.data_manager.tableClicked.connect(self.set_slider_Value)

    def on_slider_released(self):
        value = self.slider.value()
        if value == 0 :
            self.slider.setMinimum(-int(RESOL))
            self.slider.setMaximum(int(RESOL))
        else :
            self.slider.setMinimum(int(value-(abs(value)*0.2)))
            self.slider.setMaximum(int(value+(abs(value)*0.2)))
        self.data_manager.sliderMoved.emit(value)
        
    def slider_moved(self, value):
        self.data_manager.sliderMoved.emit(value)
    
    def set_slider_Value(self, value):
        value = int(value*RESOL) # Resolution : 소수점 4째 자리까지 본다. slider가 int밖에 조절 못하므로 int로 변환
        if value == 0 :
            self.slider.setMinimum(-int(RESOL))
            self.slider.setMaximum(int(RESOL))
        else :
            self.slider.setMinimum(int(value-(abs(value)*0.2)))
            self.slider.setMaximum(int(value+(abs(value)*0.2)))
        self.slider.setValue(value)
        
class PlotWindow(QtWidgets.QMainWindow):
    # 추가할 것 : 더블클릭하여 X축, Y축 조절, 데이터 및 모델 추가, 어떤 특성(R, T, sigma 등) 을 그릴지 선택
    # Plot line의 모양, 두께, 색도 선택할 수 있도록.
    def __init__(self, main, data_manager):
        super().__init__(main)
        self.data_manager = data_manager
        self.data_manager.subscribe_plot(self)
        uic.loadUi('./ui/Plot.ui', self)
        self.Canvas = PlotCanvas(self, data_manager = self.data_manager, width=5, height=4)   
        centralwidget = QtWidgets.QWidget()  # centralWidget으로 사용할 새 위젯 생성
        layout = QtWidgets.QVBoxLayout()  # centralWidget의 레이아웃을 설정
        layout.addWidget(self.Canvas)  # 캔버스 추가
        centralwidget.setLayout(layout)  # 위젯에 레이아웃 설정
        self.setCentralWidget(centralwidget)  # centralWidget 설정
        
class PlotCanvas(FigureCanvas):
    plotSignal = pyqtSignal(list)

    def __init__(self, parent=None, data_manager=None,width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        FigureCanvas.__init__(self, fig)
        self.data_manager = data_manager
        self.setParent(parent)
        self.axes.set_xlim(*Xrange_default)
        self.axes.set_ylim(*Yrange_default)
        self.draw()
        self.mpl_connect('button_press_event', self.on_double_click) #더블클릭시 수행
        self.graphProperty = graphProperty(self, data_manager = self.data_manager)
        
        self.modelLines = []
        # self.dataLines = []
        
    # 그래프 더블클릭 이벤트 정의
    def on_double_click(self, event):
        if event.dblclick:
            self.open_graph_property()
        
    def open_graph_property(self):
        self.graphProperty.show()


    def plot(self, Xrange, plotList): 
        # 현재 문제 : Xrange, Yrange 바꿀때마다 그린걸 계속 다시 그린다.
        # 그러면 색깔이 바뀌는 문제, line이 계속 새로 생기는 문제?....
        # 추후 해결 예정.
        for name in plotList :
            if name in self.data_manager.getdataNames() : 
                data = self.data_manager.getData(name)
                w, data = data
                line = self.axes.plot(w, data)
                # self.dataLines.append(line) 위의 문제 해결시 다시 복구?
                # data의 line을 계속 추적해서 관리할 필요가 있을지?
            else : # 모델의 경우 plot하기
                modelname = name.split(']')[-1]
                # name의 모델 앞의 [dtype] 제거. graphProperty의 show_datas 참고
                modelData = self.data_manager.getmodelData(modelname, Xrange=Xrange)
                w, modelData = modelData
                modelLine, = self.axes.plot(w, modelData)
                # 마찬가지로 model의 fitLine 
                for line in self.modelLines :
                    if line['name'] == name : del line
                self.modelLines.append({'name' : name, 'Xrange' : Xrange,'Line' : modelLine})
        self.draw()

    def update_plot(self, modelname):
        for line in self.modelLines :
            if modelname in line['name'] :
                w, modelData = self.data_manager.getmodelData(modelname, Xrange=line['Xrange'])
                line['Line'].set_ydata(modelData)
        self.draw()


class graphProperty(QtWidgets.QDialog):
    def __init__(self, Canvas, data_manager):
        super().__init__(Canvas)
        self.Canvas = Canvas
        self.Xrange = (0., 5000.) # 초기값 우선 넣어놓음
        self.plotList = []
        uic.loadUi('./ui/graphProperty.ui', self)
        self.data_manager = data_manager
        
        self.confirmButtonBox.accepted.connect(self.accept)
        self.confirmButtonBox.rejected.connect(self.reject)
        
        self.addplotButton.clicked.connect(self.add_to_plot)
        self.removeplotButton.clicked.connect(self.remove_from_plot)
        self.dtypebuttonGroup.buttonClicked.connect(self.show_datas)
        
    def add_to_plot(self) :
        selected_datas = self.dataListWidget.selectedItems()
        if selected_datas :
            for data in selected_datas :
                self.plotListWidget.addItem(data.text())
                row = self.dataListWidget.row(data)
                self.dataListWidget.takeItem(row)
    
    def remove_from_plot(self) :
        selected_datas = self.plotListWidget.selectedItems()
        if selected_datas :
            for data in selected_datas :
                self.dataListWidget.addItem(data.text())
                row = self.plotListWidget.row(data)
                self.plotListWidget.takeItem(row)   
                
    def show_datas(self, dtypebutton):
        self.dataListWidget.clear()
        dtype = dtypebutton.text()
        dataname = self.data_manager.getdataNames()
        modelname = self.data_manager.getmodelNames()
        
        plotlist = []
        for i in range(self.plotListWidget.count()) :
            plotlist.append(self.plotListWidget.item(i).text())
        for name in dataname :
                if (name not in plotlist) and (dtype in name) : self.dataListWidget.addItem(name)
        for name in modelname :
            self.dataListWidget.addItem('['+dtype+']' + name)

    def accept(self):
        # Update Canvas axis range
        xmin = float(self.Xmin.text())
        xmax = float(self.Xmax.text())
        ymin = float(self.Ymin.text())
        ymax = float(self.Ymax.text())
        self.Canvas.axes.set_xlim(xmin, xmax)
        self.Canvas.axes.set_ylim(ymin, ymax)
        self.Canvas.draw()
        self.plotList = [self.plotListWidget.item(i).text() for i in range(self.plotListWidget.count())]
        # x 범위는 Fit data의 plot을 위해 보낸다
        self.Xrange = (xmin, xmax)
        self.Canvas.plot(self.Xrange,self.plotList)
        self.dataListWidget.clear()
        super().accept()
        
    def reject(self):
        self.dataListWidget.clear()
        super().reject()

def main():
    app = QtWidgets.QApplication(sys.argv)
    ex = App()
    ex.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
