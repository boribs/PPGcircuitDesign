'''

Created Date: Thursday, May 2nd 2024, 11:32:14 pm
Author: Gerardo

Copyright (c) 2024 Your Company
'''

# Importación de bibliotecas necesarias
import numpy as np
from scipy import signal, stats
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui

# Carga de datos desde un archivo CSV
datapath = r"C:\Users\gerar\OneDrive\Escuela\ICAT\PPGcircuitDesign\data\measure_2024-05-06_13-47-22\GerardoIndice128_data_2024-05-06_13-47-22.csv"
datapath2 = r"C:\Users\gerar\OneDrive\Escuela\ICAT\PPGcircuitDesign\data\measure_2024-05-06_13-45-20\GerardoIndice64_data_2024-05-06_13-45-20.csv"
data = np.loadtxt(datapath, delimiter=',',skiprows=1)
fs = 128 # Hz
N = len(data)
T = 1 / fs
bin_size = fs / N
y1 = data[: , 1]
t = data[: , 0]
faxis = np.linspace(0, fs-bin_size, len(y1)) # Eje de frecuencia

# Creación de una ventana para visualizar las señales
plt = pg.plot()
plt.showGrid(x=True, y=True)
plt.setWindowTitle("128Hz")
plt.addLegend()
plt.setLabel('left', 'mmHg', units='V')
plt.setLabel('bottom', 'Time', units='s')

# Filtrado de la señal
f5 = 5  # Frecuencia de corte para el filtro pasa bajos
bLP, aLP = signal.butter(4, f5 / fs * 2, 'lowpass')  # Diseño del filtro pasa bajos
yfLP = signal.lfilter(bLP, aLP, y1)  # Aplicación del filtro pasa bajos

f05 = 0.3  # Frecuencia de corte para el filtro pasa altos
bHP, aHP = signal.butter(2, f05 / fs * 2, 'highpass')  # Diseño del filtro pasa altos
yfHP = signal.lfilter(bHP, aHP, yfLP)  # Aplicación del filtro pasa altos
yfBP = yfLP-yfHP  # Señal filtrada pasa banda

#Notch filter   ? Necesary
notchFreq = 50.0
qF = 20.0
b_notch, a_notch = signal.iirnotch(notchFreq, qF, fs)
fNotch = signal.filtfilt(b_notch, a_notch, yfBP)

plt.plot(faxis, y1, pen='b', name ='Señal original')
plt.plot(faxis, yfHP, pen='y', name ='HighPass Filter')
plt.plot(faxis, fNotch, pen='r', name ='Notch Filter')


# Cálculo de picos máximos y mínimos locales
adj = 0.005

localMax, _ = signal.find_peaks(yfBP, prominence=adj)
localMin, _ = signal.find_peaks(-yfBP, prominence=adj)

# Cálculo de características de la señal
yMax = yfBP[localMax]
yMin = yfBP[localMin]
tMaximas  = faxis[localMax]
tMinimas = faxis[localMin]


plt2 = pg.plot()
plt2.showGrid(x=True, y=True)
plt2.addLegend()
plt2.setWindowTitle("Maximos y minimos 128Hz")
plt2.setLabel('left', 'Voltage', units='[V]')
plt2.setLabel('bottom', 'Time', units='[s]')

# Graficar la señal filtrada y los puntos de máximos y mínimos locales
plt2.plot(faxis, yfBP, pen='y', name='Passband Filter')
plt2.plot(faxis[localMax], yMax, pen=None, symbol='o', symbolBrush='g', name='Maximos', symbolSize=4)
plt2.plot(faxis[localMin], yMin, pen=None, symbol='o', symbolBrush='r', name='Minimos', symbolSize=4)
