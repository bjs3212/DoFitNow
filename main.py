# -*- coding: utf-8 -*-

import sys
import numpy as np
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
    sliderChanged = pyqtSignal(int)
    
    def __init__(self):
        super().__init__()
        uic.loadUi('./ui/dfn.ui', self)
        self.modelButton = self.findChild(QtWidgets.QPushButton, 'modelButton')
        self.plotButton = self.findChild(QtWidgets.QPushButton, 'plotButton')
        self.modelButton.clicked.connect(self.open_model_window)
        self.plotButton.clicked.connect(self.open_plot_window)
        
        self.models = []
        self.plots = []
        self.ParAdjust = ParAdjust(self)

    def open_model_window(self):
        ParTable_ = ParTable(self)  # 새 창 인스턴스 생성
        ParTable_.show()         # 새 창 보여주기
        self.models.append(ParTable_)
        
        self.ParAdjust.show()
    
    def open_plot_window(self):
        PlotWindow_ = PlotWindow(self)  # 새 창 인스턴스 생성
        PlotWindow_.show()         # 새 창 보여주기
        self.models.append(PlotWindow_)

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
        self.main.sliderChanged.connect(self.update_cell_value)

    def cell_clicked(self, row, column):
        # 클릭된 셀의 값을 가져옵니다.
        value = self.parameters[row][column] if self.table.item(row, column) else ""
        self.rowcolumn = (row,column)
        self.main.tableClicked.emit(value)
        
    def update_cell_value(self, value):
        # 현재 선택된 셀의 값을 업데이트
        current_item = self.table.currentItem()
        if current_item:
            value = value/10000.0
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
        self.slider.valueChanged.connect(self.slider_value_changed)
        self.slider.sliderReleased.connect(self.on_slider_released)
        self.main.tableClicked.connect(self.set_slider_Value)

    def on_slider_released(self):
        value = self.slider.value()
        if value == 0 :
            self.slider.setMinimum(-10000)
            self.slider.setMaximum(10000)
        else :
            self.slider.setMinimum(int(value*0.8))
            self.slider.setMaximum(int(value*1.2))
        self.main.sliderChanged.emit(value)
        
    def slider_value_changed(self, value):
        self.main.sliderChanged.emit(value)
    
    def set_slider_Value(self, value):
        value = int(value*10000) # Resolution : 소수점 4째 자리까지 본다. slider가 int밖에 조절 못하므로 int로 변환
        self.slider.setValue(value)
        if value == 0 :
            self.slider.setMinimum(-10000)
            self.slider.setMaximum(10000)
        else :
            self.slider.setMinimum(int(value*0.8))
            self.slider.setMaximum(int(value*1.2))
        
    def update_table(self,value):
        self.main.sliderChanged.emit(value)
        
        
class PlotWindow(QtWidgets.QMainWindow):
    # 추가할 것 : 더블클릭하여 X축, Y축 조절, 데이터 및 모델 추가, 어떤 특성(R, T, sigma 등) 을 그릴지 선택
    # Plot line의 모양, 두께, 색도 선택할 수 있도록.
    def __init__(self, main):
        super().__init__()
        self.main = main
        uic.loadUi('./ui/Plot.ui', self)
        
        

def main():
    app = QtWidgets.QApplication(sys.argv)
    ex = App()
    ex.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
