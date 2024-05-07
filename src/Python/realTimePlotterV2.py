"""
Created on Fri Apr 19 14:33:31 2024

@author: GerardoROCA
"""

from scipy import signal
import importlib.util
import sys
import time
import serial
import csv
import numpy as np
import pyqtgraph as pg
from PyQt5.QtWidgets import (
    QMessageBox, QApplication, QMainWindow, QVBoxLayout, QWidget,
    QGridLayout, QPushButton, QComboBox, QFileDialog, QCheckBox,
    QLabel, QLineEdit
)
from PyQt5.QtCore import QThread, pyqtSignal, Qt
import serial.tools.list_ports

required_libraries = [
    "serial",
    "csv",
    "numpy",
    "pyqtgraph",
    "PyQt5",
    "os"
]

missing_libraries = [
    lib for lib in required_libraries if importlib.util.find_spec(lib) is None]

if missing_libraries:
    print("Las siguientes bibliotecas están ausentes y deben ser instaladas:")
    for lib in missing_libraries:
        print(lib)
    sys.exit(1)


class SerialReader(QThread):
    data_received = pyqtSignal(np.ndarray)

    def __init__(self, serial_port, baudrate, plot_widget):
        super().__init__()
        self.serial_port = serial_port
        self.baud_rate = baudrate
        self.plot_widget = plot_widget
        self.max_attempts = 3
        self.attempts = 0
        self.dataValues = 1
        self.is_reading = True
        self.multiLanes = False
        self.start_time = time.time()
        self.current_time = []
        self.data_value = []
        self.data_value_extra = []
        self.fileName = "default"


    def run(self):
        while self.attempts < self.max_attempts:
            try:
                with serial.Serial(self.serial_port, self.baud_rate) as ser:
                    self.serial_connection = ser
                    while self.is_reading:
                        data = ser.readline().decode('utf-8').strip()
                        try:
                            if ',' in data:  
                                data_values = data.split(', ')
                                if len(data_values) == 2:
                                    self.dataValues = 2
                                    timeOn = len(self.current_time)
                                    self.current_time.append(timeOn)
                                    self.data_value.append(
                                        float(data_values[1]))
                                    self.data_received.emit(
                                        np.array([float(data_values[1])]))
                                elif len(data_values) == 3:
                                    self.dataValues = 3
                                    timeOn = len(self.current_time)
                                    self.current_time.append(timeOn)
                                    self.data_value.append(
                                        float(data_values[1]))
                                    self.data_value_extra.append(
                                        float(data_values[2]))
                                    self.data_received.emit(
                                        np.array([float(data_values[1]), float(data_values[2])]))
                                else:
                                    print(
                                        "Error: Incorrect number of values for multilane data")
                            else:
                                data = float(data)
                                timeOn = len(self.current_time)
                                self.current_time.append(timeOn)
                                self.data_value.append(data)
                                self.data_received.emit(np.array([data]))
                        except ValueError as e:
                            print("Error converting data to float:", e)

            except Exception as e:
                print("Error reading serial data:", e)

                self.attempts += 1
                if self.attempts >= self.max_attempts:
                    print("Max connection attempts reached.")
                    return
                else:
                    print(f"Retrying connection... Attempt {
                            self.attempts}/{self.max_attempts}")
                    time.sleep(3)
        if self.serial_connection is not None:
            self.serial_connection.close()

    def saveData(self):
        if self.data_value:
            import datetime
            import os
            options = QFileDialog.Options()
            folder_path = QFileDialog.getExistingDirectory(
                None, "Select Folder to Save Image", options=options)
            if folder_path:
                os.makedirs(folder_path, exist_ok=True)
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                subfolder_name = f"measure_{timestamp}"
                subfolder_path = os.path.join(folder_path, subfolder_name)
                os.makedirs(subfolder_path, exist_ok=True)
                filename_csv = os.path.join(
                    subfolder_path, f"{self.fileName}_data_{timestamp}.csv")
                filename_txt = os.path.join(
                    subfolder_path, f"{self.fileName}_proteusSample_{timestamp}.txt")
                filename_png = os.path.join(
                    subfolder_path, f"{self.fileName}_Graph_{timestamp}.png")
                
                if self.dataValues < 3:
                    with open(filename_csv, mode='w', newline='') as file:
                        writer = csv.writer(file)
                        writer.writerow(['time', 'value1'])
                        for time, data in zip(self.current_time, self.data_value):
                            # relative_time = time - min_time
                            writer.writerow([time, data])
                    print("Data saved")

                    with open(filename_txt, 'w') as txtfile:
                        for i in range(len(self.data_value)):
                            txtfile.write(f"{self.current_time[i]}\t{
                                            self.data_value[i]}\n")
                    self.plot_widget.save_image(filename_png)
                else:
                    with open(filename_csv, mode='w', newline='') as file:
                        writer = csv.writer(file)
                        writer.writerow(['time', 'value1', 'value2'])
                        for time, data1, data2 in zip(self.current_time, self.data_value, self.data_value_extra):
                            # relative_time = time - min_time
                            writer.writerow([time, data1, data2])
                    print("Data saved")
                    self.plot_widget.save_image(filename_png)
                return filename_csv

    def stop_reading(self):
        self.is_reading = False

    def start_reading(self):
        self.is_reading = True
        self.current_time = []
        self.data_value = []
        self.data_value_extra = []
        print("Values restored")


class dataAnalysis:
    def __init__(self, data_path, sampleRate):
        self.data = np.loadtxt(data_path, delimiter=',', skiprows=1)
        self.fs = float(sampleRate)
        self.N = len(self.data)
        self.T = 1/self.fs
        self.bin_size = self.fs/self.N
        self.y1 = self.data[:, 1]
        self.t = self.data[:, 0]
        self.faxis = np.linspace(0, self.fs-self.bin_size, len(self.y1))

    def filter60():
        # Se añade esta linea de texto
        pass

    def bloodPreasure(self):

        f5 = 5
        bLP, aLP = signal.butter(4, f5/self.fs*2, 'lowpass')  # Filtro pasa bajo
        yfLP = signal.lfilter(bLP, aLP, self.y1)  # Aplicar filtro pasa bajo

        f05 = 0.3
        bHP, aHP = signal.butter(2, f05/self.fs*2, 'highpass')  # Filtro pasa alto
        yfHP = signal.lfilter(bHP, aHP, yfLP)  # Aplicar filtro pasa alto

        yfBP = yfLP - yfHP  # Obtener la señal filtrada

        # Configuración de la gráfica
        plt = pg.plot()
        plt.showGrid(x=True, y=True)
        plt.setWindowTitle("Señales filtradas")
        plt.resize(1500, 800)
        plt.addLegend()
        plt.setLabel('left', 'Valores Verticales', units='V')
        plt.setLabel('bottom', 'Datos', units='s')
        
        plt.plot(self.faxis, yfBP, pen ='g', name ='Señal filtrada')

        indexGlobalMax = np.argmax(yfBP)
        newfHP = yfHP[indexGlobalMax:]
        self.faxis = self.faxis[indexGlobalMax:]

        localMax = []
        adj = 0.9
        while (len(localMax) < 10) | ((len(localMax) > 50)):
            localMax, _ = signal.find_peaks(newfHP, prominence=adj)
            localMin, _ = signal.find_peaks(-newfHP, prominence=adj)
            if (len(localMax) < 10):
                adj -= 0.05
            if (len(localMax) > 50):
                adj += 0.05

        if len(localMin) > len(localMax):
            localMin = localMin[1:]
        elif len(localMin) < len(localMax):
            localMax = localMax[1:]

        yMax = newfHP[localMax]
        yMin = newfHP[localMin]
        maxOscilometric = np.argmax(newfHP)

        delta = []

        for i in range(len(localMax)-1):
            delta.append(
                round(self.faxis[localMin[i+1]] - self.faxis[localMin[i]], 3))

        deltaFiltrada = []
        indicesFiltrada = []

        for i in range(len(delta)):
            if delta[i] < 2:
                deltaFiltrada.append(delta[i])
                indicesFiltrada.append(i)

        indicesInteres = []
        for i in range(len(deltaFiltrada)-1):
            if (indicesFiltrada[i+1]-indicesFiltrada[i]) == 1:
                indicesInteres.append(indicesFiltrada[i])
            elif (indicesFiltrada[i]-indicesFiltrada[i-1]) == 1:
                indicesInteres.append(indicesFiltrada[i])

        sistoleFilter = yfBP[indexGlobalMax+localMax[indicesInteres[0]]]
        diastoleFilter = yfBP[indexGlobalMax+localMax[indicesInteres[-1]]]
        mapsdFilter = (sistoleFilter-diastoleFilter/3)+diastoleFilter

        print("Sistole: ", sistoleFilter)
        print("Diastole: ", diastoleFilter)
        print("MAP: ", mapsdFilter)

        intervalos_RR = np.diff(self.faxis[localMin[indicesInteres]])

        frecuencia_cardiaca_bpm = np.mean(intervalos_RR * 60)

        # Imprimir la frecuencia cardíaca promedio
        print("Frecuencia cardíaca promedio (BPM):", (frecuencia_cardiaca_bpm))

        sistole = yfBP[indexGlobalMax+maxOscilometric]/0.75
        diastole = yfBP[indexGlobalMax+maxOscilometric]*0.7
        mapsd = (sistole-diastole/3)+diastole

        print("Sistole: ", sistole)
        print("Diastole: ", diastole)
        print("MAP: ", mapsd)

        plt2 = pg.plot()
        plt2.showGrid(x=True, y=True)
        plt2.addLegend()
        plt2.setWindowTitle("Local Maxima and Minima")
        plt2.setLabel('left', 'BloodPreasure', units='mmHg')
        plt2.setLabel('bottom', 'Time', units='s')
        
        if sistoleFilter < 120:
            state = "Normal"
        elif (sistoleFilter >= 130 and sistoleFilter <= 139):
            state = "Subóptima"
        elif (sistoleFilter >= 140 and sistoleFilter <= 159) :
            state = "Hipertensión grado 1 (Límite)"
        elif (sistoleFilter >= 160 and sistoleFilter <= 179):
            state = "Hipertensión grado 2"
        elif sistoleFilter >= 180:
            state = "Hipertensión grado 3"
        else:
            state = "No clasificado"



        # Graficar la señal filtrada y los puntos de máximos y mínimos locales
        plt2.plot(self.faxis, newfHP, pen='y', name='Passband Filter')
        plt2.plot(self.faxis[localMax], yMax, pen=None, symbol='o',
                  symbolBrush='g', name='Local Maxima', symbolSize=2)
        plt2.plot(self.faxis[localMin], yMin, pen=None, symbol='o',
                  symbolBrush='r', name='Local Minima', symbolSize=2)

        return sistoleFilter, diastoleFilter, mapsd, frecuencia_cardiaca_bpm, state


class SerialCtrl():
    def __init__(self):
        self.com_list = []

    def getCOMlist(self):
        ports = serial.tools.list_ports.comports()
        self.com_list = [com[0] for com in ports]
        self.com_list.insert(0, "-")


class RealTimePlot(QWidget):
    def __init__(self, serialCom, baudrate):
        super().__init__()

        self.plot_widget = pg.PlotWidget()
        self.curve = self.plot_widget.plot(pen='b')
        self.curve_extra = None
        self.plot_widget.setTitle("Measure vs Time")
        self.plot_widget.setLabel("left", "Measure (V)")
        self.plot_widget.setLabel("bottom", "data")
        self.plot_widget.showGrid(x=True, y=True)
        self.is_reading = True
        self.max_data_points = 15000
        self.data_count = 0

        layout = QVBoxLayout()
        layout.addWidget(self.plot_widget)
        self.setLayout(layout)

        self.x = np.array([])
        self.y = np.array([])
        self.y_extra = np.array([])

        self.serial_reader = SerialReader(serialCom, baudrate, self)
        self.serial_reader.data_received.connect(self.update_plot)
        self.serial_reader.start()

    def update_plot(self, data):
        self.x = np.append(self.x, len(self.x))
        self.y = np.append(self.y, data[0])
        self.curve.setData(self.x[-self.max_data_points:],
                           self.y[-self.max_data_points:])

        if len(data) >= 2:
            if self.curve_extra is None:
                self.curve_extra = self.plot_widget.plot(pen='r')
            self.y_extra = np.append(self.y_extra, data[1])
            self.y_extra = self.y_extra[-self.max_data_points:]

            x_extra = self.x[-len(self.y_extra):]
            self.curve_extra.setData(x_extra, self.y_extra)

    def save_image(self, file_name):
        if file_name:
            image = self.plot_widget.grab()
            image.save(file_name)

    def reset_plot(self):
        self.x = np.array([])
        self.y = np.array([])
        self.y_extra = np.array([])
        self.x_extra = np.array([])
        self.curve.setData(self.x, self.y)


class mainWindow(QMainWindow):
    def __init__(self):
        super(mainWindow, self).__init__()
        self.serial = serial
        self.text = "default"
        self.sampleRate = 64

        self.setWindowTitle("Real Plotter V.2")
        self.resize(1200, 600)

        self.layout = QVBoxLayout()
        self.layout = QGridLayout()

        comment_label = QLabel("""
        @author: GerardoROCA
                        GUI para la recoleccion y almacenamiento de datos serial
            Al seleccionar multiLanes se espera que el serial.print del arduino tenga la siguiente estructura
                        -> dato1, dato2, dato3 ó -> dato1, dato2
            Serial.print(dato1,4);  Serial.print(", "); Serial.print(dato2, 5); Serial.print(", "); Serial.println(dato3, 5)
                            
            En caso de no seleccionar multiLanes se espera que sea
                        -> dato1             (Grafica el dato1)
        """)
        self.layout.addWidget(comment_label, 2, 0, 1, 0)

        self.button = QPushButton("Start")
        self.button.setFixedSize(200, 150)
        self.button.clicked.connect(self.show_state)

        self.buttonRefresh = QPushButton("Refresh")
        self.buttonRefresh.setFixedSize(200, 150)
        self.buttonRefresh.clicked.connect(self.refreshCom)

        self.lanesCheck = QCheckBox("MultiLanes")
        self.lanesCheck.setFixedSize(200, 150)
        self.lanesCheck.setCheckState(Qt.Checked)
        self.lanes = True
        self.lanesCheck.stateChanged.connect(self.multiLanesSel)

        self.comList = QComboBox()
        self.update_com_list()

        self.baudList = QComboBox()
        self.baudList.addItems(["-", "300", "600", "1200", "2400", "4800",
                                "9600", "14400", "19200", "28800", "38400", "56000",
                                "57600", "115200", "128000", "256000"])

        self.layout.addWidget(self.button, 0, 0)
        self.layout.addWidget(self.buttonRefresh, 0, 1)
        self.layout.addWidget(self.lanesCheck, 0, 2)
        self.layout.addWidget(self.comList, 1, 0)
        self.layout.addWidget(self.baudList, 1, 1)

        widget = QWidget()
        widget.setLayout(self.layout)
        self.setCentralWidget(widget)

        self.plotWidget = None

    def show_state(self):
        comSelected = self.comList.currentText()
        baudSelected = self.baudList.currentText()
        lanes = self.lanes
        self.connection_successful = False
        while not self.connection_successful:
            if comSelected != "-" and baudSelected != "-":
                try:
                    self.layout.removeWidget(self.button)
                    self.layout.removeWidget(self.baudList)
                    self.layout.removeWidget(self.comList)
                    self.layout.removeWidget(self.buttonRefresh)
                    self.layout.removeWidget(self.lanesCheck)
                    self.lanesCheck.deleteLater()
                    self.buttonRefresh.deleteLater()
                    self.comList.deleteLater()
                    self.baudList.deleteLater()
                    self.button.deleteLater()

                    self.resize(1200, 920)
                    
                    self.layout = QGridLayout()
                    self.plotWidget = RealTimePlot(comSelected, baudSelected)
                    self.plotWidget.serial_reader.multiLanes = lanes
                    self.layout.addWidget(self.plotWidget, 0, 0, 1, 0)
                    self.saveButton = QPushButton("SaveData")
                    self.analysisButton = QPushButton("StartAnalysis")
                    self.closeButton = QPushButton("Close")
                    self.restartButton = QPushButton("Restart")
                    
                    self.saveButton.setFixedSize(200, 150)
                    self.saveButton.clicked.connect(self.saveData)
                    self.analysisButton.setFixedSize(200, 150)
                    self.analysisButton.clicked.connect(self.analysis)
                    self.closeButton.setFixedSize(200, 150)
                    self.closeButton.clicked.connect(self.close)
                    self.restartButton.setFixedSize(200, 150)
                    self.restartButton.clicked.connect(self.restart_program)
                    
                    self.layout.addWidget(self.saveButton, 1, 0)
                    self.layout.addWidget(self.analysisButton, 1, 1)
                    self.layout.addWidget(self.closeButton, 1, 2)
                    self.layout.addWidget(self.restartButton, 1, 3)
                    self.connection_successful = True
                    widget = QWidget()
                    widget.setLayout(self.layout)
                    self.setCentralWidget(widget)
                    self.textInput = QLineEdit()
                    self.textInput.setMaxLength(25)
                    self.textInput.setPlaceholderText("Enter your file name")
                    self.textInput.textChanged.connect(self.text_changed)
                    self.textInput.textEdited.connect(self.text_edited)
                    self.layout.addWidget(self.textInput, 1, 4)
                    self.label_sistolic = QLabel("Systolic BP: -")
                    self.label_diastolic = QLabel("Diastolic BP: -")
                    self.label_mapsd = QLabel("MAP : - , ST: ")
                    self.label_frecuencia_cardiaca_bpm = QLabel("BPM : -")
                    self.layout.addWidget(self.label_sistolic, 3, 0)
                    self.layout.addWidget(self.label_diastolic, 3, 1)
                    self.layout.addWidget(self.label_mapsd, 3, 2)
                    self.layout.addWidget(
                        self.label_frecuencia_cardiaca_bpm, 3, 3)

                    self.setCentralWidget(widget)

                    comment_label = QLabel("""
                    @author: GerardoROCA
                        "SaveData" guardara los datos en el momento que tu lo decidas,
                            es decir que se seguiran almacenando datos aunque lo 
                                           estes guardando
                        "StartAnalysis" detendra la recoleccion de datos y los guardara 
                           para un analisis posterior (por el momento 
                           no existe analisis posterior por lo que solo 
                            detendra y guardara los datos)
                        "Close" cerrara el programa
                        "Restart" volver a recolectar datos emepzando la grafica desde cero         
                    """)
                    self.layout.addWidget(comment_label, 2, 0, 1, 0)

                    self.textInput_sampleRate = QLineEdit()
                    self.textInput_sampleRate.setMaxLength(25)
                    self.textInput_sampleRate.setPlaceholderText(
                        "Enter your sample rate")
                    self.textInput_sampleRate.textChanged.connect(
                        self.text_changed_sampleRate)
                    self.textInput_sampleRate.textEdited.connect(
                        self.text_edited_sampleRate)
                    self.layout.addWidget(self.textInput_sampleRate, 2, 4)

                except Exception as e:
                    QMessageBox.warning(
                        self, "Warning", f"Failed to establish connection: {str(e)}")
                    return
            else:
                QMessageBox.warning(
                    self, "Warning", "Please select a valid COM port and baudrate.")
                return

    def refreshCom(self):
        self.update_com_list()

    def saveData(self):
        self.plotWidget.serial_reader.fileName = self.text
        self.plotWidget.serial_reader.saveData()

    def multiLanesSel(self, s):
        self.lanes = (s == Qt.Checked)

    def analysis(self):
        self.plotWidget.serial_reader.stop_reading()
        self.plotWidget.serial_reader.fileName = self.text
        self.data_path = self.plotWidget.serial_reader.saveData()
        if self.data_path:
            self.data_analysis = dataAnalysis(self.data_path, self.sampleRate)
            sistoleFilter, diastoleFilter, mapsd, frecuencia_cardiaca_bpm, state = self.data_analysis.bloodPreasure()
            self.label_sistolic.setText(f"Systolic BP: {sistoleFilter:.2f}")
            self.label_diastolic.setText(f"Diastolic BP: {diastoleFilter:.2f}")
            self.label_mapsd.setText(f"MAP : {mapsd:.3f}, ST: {str(state)}")

            self.label_frecuencia_cardiaca_bpm.setText(
                f"BPM: {frecuencia_cardiaca_bpm:.2f}")
        else:
            print("Error on data file, try again")


    def text_changed(self, s):
        self.text = s

    def text_edited(self, s):
        self.text = s

    def text_changed_sampleRate(self, s):
        self.sampleRate = s

    def text_edited_sampleRate(self, s):
        self.sampleRate = s

    def close(self):
        reply = QMessageBox.question(self, 'Confirmación', '¿Estás seguro de que deseas cerrar la aplicación?',
                                        QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            QApplication.quit()

    def restart_program(self):
        if self.plotWidget:
            self.plotWidget.reset_plot()
            self.data_path = None
            try:
                self.plotWidget.serial_reader.start_reading()
            except:
                pass

    def update_com_list(self):
        serial_ctrl = SerialCtrl()
        serial_ctrl.getCOMlist()
        self.comList.clear()
        self.comList.addItems(serial_ctrl.com_list)


def main():

    app = QApplication(sys.argv)

    window = mainWindow()

    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
