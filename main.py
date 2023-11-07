# -*- coding: utf-8 -*-

RESOL = 10.0 ** (4) # 10 ** (N) 은 각 parameter에 N개의 소수점을 포함하겠다는 뜻

import sys
import numpy as np
import pandas as pd
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QTableWidgetItem
from PyQt5.QtCore import pyqtSignal, Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

def drude_sigma(w, wp, g) :
    return (wp*wp/(4*np.pi))*(1/(g-1j*w))

def local_drude_sigma(w, sigma_drude, g, C) :
    return sigma_drude * (1 + C*(1-(w*w/(g*g)))/(1+(w*w/(g*g))) )

# 메인 윈도우가 될 App 클래스
class App(QtWidgets.QMainWindow):
    # 추가할 것 : 메뉴 바, 각 윈도우(Fit, Plot, Model 등) 여는 버튼, 파일 업로드 기능
    tableClicked = pyqtSignal(float)
    sliderMoved = pyqtSignal(int)
    
    def __init__(self):
        super().__init__()
        uic.loadUi('./ui/dfn.ui', self)
        self.modelButton = self.findChild(QtWidgets.QPushButton, 'modelButton')
        self.plotButton = self.findChild(QtWidgets.QPushButton, 'plotButton')
        self.uploadButton = self.findChild(QtWidgets.QPushButton, 'uploadButton')
        self.modelButton.clicked.connect(self.open_model_window)
        self.plotButton.clicked.connect(self.open_plot_window)
        self.uploadButton.clicked.connect(self.uploadDataFile)
        
        self.models = []
        self.plots = []
        self.datas = []
        self.ParAdjust = ParAdjust(self)

    def open_model_window(self):
        ParTable_ = ParTable(self)
        ParTable_.show()
        self.models.append(ParTable_)
        
        self.ParAdjust.show()
    
    def open_plot_window(self):
        PlotWindow_ = PlotWindow(self)
        PlotWindow_.show()
        self.models.append(PlotWindow_)
        
    def uploadDataFile(self):
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        fileName, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Open Data File", "", "All Files (*);;Text Files (*.txt)", options=options)
        if fileName: # 파일 타입에 따라 다르게 받는 것 구현 예정
            # 첫 번째 열은 X축, 나머지 열은 Y축 데이터로 생각한다.
            data = pd.read_csv(fileName, delimiter=' ')
            self.datas.append(data)
            print(data.head())
            
# Fit에 필요한 변수들을 저장할 Table
class ParTable(QtWidgets.QMainWindow):
    # 추후 추가할 것 : 테이블 행 추가, 각 행 별로 무슨 모델(lorentzian, drude 등) 쓸지 결정란 추가
    # Parameter (열) 도 모델에 따라서 추가되도록
    def __init__(self, main):
        super().__init__()
        self.main = main
        uic.loadUi('./ui/ParTable.ui', self)
        self.table = self.findChild(QtWidgets.QTableWidget, 'ParTable')
        self.parameters = np.zeros((1,3), dtype=float) # each element is C, wp, Gamma
        self.initialize()
    
    def initialize(self):
        self.table.setItem(0,0, QTableWidgetItem(f"{self.parameters[0][0]:0.2f}"))
        self.table.setItem(0,1, QTableWidgetItem(f"{self.parameters[0][1]:0.2f}"))
        self.table.setItem(0,2, QTableWidgetItem(f"{self.parameters[0][2]:0.2f}"))
        
        self.table.cellClicked.connect(self.cell_clicked)
        self.main.sliderMoved.connect(self.update_cell_value)

    def cell_clicked(self, row, column):
        # 클릭된 셀의 값을 가져옵니다.
        value = self.parameters[row][column] if self.table.item(row, column) else ""
        self.rowcolumn = (row,column)
        self.main.tableClicked.emit(value)
        
    def update_cell_value(self, value):
        # 현재 선택된 셀의 값을 업데이트
        current_item = self.table.currentItem()
        if current_item:
            value = value/RESOL
            row, column = self.rowcolumn
            self.parameters[row][column]=value
            current_item.setText(str(f"{value:0.2f}"))
            
    
# 각 Parameter를 Slider형태로 조절하는 창    
class ParAdjust(QtWidgets.QMainWindow):
    # 추가할 것 : Min Max 입력, 조절을 Linear로 할지 exponential하게 할지 선택?
    def __init__(self, main):
        super().__init__()
        self.main = main
        uic.loadUi('./ui/ParAdjust.ui', self)
        self.slider = self.findChild(QtWidgets.QSlider, 'ParAdjust_Slider')
        self.slider.sliderMoved.connect(self.slider_moved)
        self.slider.sliderReleased.connect(self.on_slider_released)
        self.main.tableClicked.connect(self.set_slider_Value)

    def on_slider_released(self):
        value = self.slider.value()
        if value == 0 :
            self.slider.setMinimum(-int(RESOL))
            self.slider.setMaximum(int(RESOL))
        else :
            self.slider.setMinimum(int(value-(abs(value)*0.2)))
            self.slider.setMaximum(int(value+(abs(value)*0.2)))
        self.main.sliderMoved.emit(value)
        
    def slider_moved(self, value):
        self.main.sliderMoved.emit(value)
    
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
    def __init__(self, main):
        super().__init__()
        self.main = main
        uic.loadUi('./ui/Plot.ui', self)
        self.Canvas = PlotCanvas(self, width=5, height=4)   
        centralwidget = QtWidgets.QWidget()  # centralWidget으로 사용할 새 위젯 생성
        layout = QtWidgets.QVBoxLayout()  # centralWidget의 레이아웃을 설정
        layout.addWidget(self.Canvas)  # 캔버스 추가
        centralwidget.setLayout(layout)  # 위젯에 레이아웃 설정
        self.setCentralWidget(centralwidget)  # centralWidget 설정
        
class PlotCanvas(FigureCanvas):

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        FigureCanvas.__init__(self, fig)
        self.setParent(parent)
        self.axes.set_xlim(0,5000)
        self.axes.set_ylim(0,1)
        self.draw()
        #self.plot()
        self.mpl_connect('button_press_event', self.on_double_click) #더블클릭시 수행

    # 그래프 더블클릭 이벤트 정의
    def on_double_click(self, event):
        if event.dblclick:
            self.open_graph_property()
        
    def open_graph_property(self):
        self.graphProperty = graphProperty(self)
        self.graphProperty.show()


    def plot(self):
        self.C = 0
        self.wp = 300 # 각 파라미터들의 초기값 설정
        self.g = 100
        self.w = np.linspace(1,10000, 10000)
        self.line1, = self.axes.plot(self.w, local_drude_sigma(self.w, drude_sigma(self.w, self.wp, self.g), self.g, self.C))
        self.axes.set_title('PyQt Matplotlib Example')
        self.draw()
        
    def plot_data(self, x, y):
        self.line2, = self.axes.plot(x,y)
        self.draw()

    def update_plot(self, par,  value):
        if par == 'C' : self.C = value/100
        elif par == 'wp' : self.wp = value
        elif par == 'g' : self.g = value
        self.line1.set_ydata(local_drude_sigma(self.w, drude_sigma(self.w, self.wp, self.g), self.g, self.C))
        self.draw()


class graphProperty(QtWidgets.QDialog):
    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas
        uic.loadUi('./ui/graphProperty.ui', self)
        
        buttons = self.findChild(QtWidgets.QDialogButtonBox, 'confirmButtonBox')
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

    def accept(self):
        # Update canvas axis range
        xmin = float(self.Xmin.text())
        xmax = float(self.Xmax.text())
        ymin = float(self.Ymin.text())
        ymax = float(self.Ymax.text())
        self.canvas.axes.set_xlim(xmin, xmax)
        self.canvas.axes.set_ylim(ymin, ymax)
        self.canvas.draw()
        super().accept()

def main():
    app = QtWidgets.QApplication(sys.argv)
    ex = App()
    ex.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
