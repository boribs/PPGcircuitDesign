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
data = np.loadtxt(r"C:\Users\gerar\OneDrive\Escuela\Semestre 2024-2\SistemasMedicionTransductores\Practica4-PresionArterial\data\dataValue1.csv", delimiter=',',skiprows=1)
fs= 80 # Hz
N = len(data)
T = 1/fs
bin_size = fs/N 
y1 = data[:,1]
t = data[:,0] 
faxis = np.linspace(0,fs-bin_size,len(y1)) # Eje de frecuencia

# Creación de una ventana para visualizar las señales
plt = pg.plot()
plt.showGrid(x = True, y = True)
plt.setWindowTitle("Filtered signals")
plt.addLegend()
plt.setLabel('left', 'mmHg', units='V') 
plt.setLabel('bottom', 'Time', units='s')

# Filtrado de la señal
f5 = 5  # Frecuencia de corte para el filtro pasa bajos
bLP, aLP = signal.butter(4, f5/fs*2, 'lowpass')  # Diseño del filtro pasa bajos
yfLP = signal.lfilter(bLP, aLP, y1)  # Aplicación del filtro pasa bajos

f05 = 0.3  # Frecuencia de corte para el filtro pasa altos
bHP, aHP = signal.butter(2, f05/fs*2, 'highpass')  # Diseño del filtro pasa altos
yfHP = signal.lfilter(bHP, aHP, yfLP)  # Aplicación del filtro pasa altos
yfBP = yfLP-yfHP  # Señal filtrada pasa banda

#Notch filter   ? Necesary
notchFreq = 50.0 
qF = 20.0
b_notch, a_notch = signal.iirnotch(notchFreq, qF, fs)
fNotch = signal.filtfilt(b_notch, a_notch, yfBP)

# plt.plot(faxis, y1, pen ='y', name ='Señal original')
# plt.plot(faxis, yfHP, pen ='y', name ='Passband Filter')
plt.plot(faxis, yfBP, pen ='g', name ='Señal filtrada')
# plt.plot(faxis, fNotch, pen ='r', name ='Notch Filter')


# Cálculo de picos máximos y mínimos locales
globalMax = np.max(yfBP) 
indexGlobalMax = np.argmax(yfBP)
newfHP = yfHP[indexGlobalMax:]
faxis = faxis[indexGlobalMax:]

localMax = []
adj = 0.9
while(len(localMax) < 10)|((len(localMax) > 50)):
    localMax, _ = signal.find_peaks(newfHP, prominence = adj)
    localMin, _ = signal.find_peaks(-newfHP, prominence = adj)
    if(len(localMax)<10):
        adj -= 0.05
    if(len(localMax)>50):
        adj += 0.05

# Ajuste de los números de picos máximos y mínimos
if len(localMin)> len(localMax):
    localMin = localMin[1:]
elif len(localMin)< len(localMax):
    localMax = localMax[1:]

# Cálculo de características de la señal
yMax = newfHP[localMax]
yMin = newfHP[localMin]
tMaximas  = t[localMax]
tMinimas = t[localMin]

maxOscilometric = np.argmax(newfHP) 

delta = []
delta2= []
# Cálculo de intervalos RR y frecuencia cardíaca
for i in range(len(localMax)-1):
    delta.append(round(faxis[localMin[i+1]] - faxis[localMin[i]], 3))
    # print(faxis[localMax[i]], delta[i], yfBP[indexGlobalMax+localMax[i]],i)

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



intervalos_RR = np.diff(faxis[localMin[indicesInteres]])

frecuencia_cardiaca_bpm = intervalos_RR * 60

# Imprimir la frecuencia cardíaca promedio
print("Frecuencia cardíaca promedio (BPM):", np.mean(frecuencia_cardiaca_bpm))

sistoleFilter = yfBP[indexGlobalMax+localMax[indicesInteres[0]]]
diastoleFilter = yfBP[indexGlobalMax+localMax[indicesInteres[-1]]]
mapsdFilter = (sistoleFilter-diastoleFilter/3)+diastoleFilter


print("Sistole: ", sistoleFilter)
print("Diastole: ", diastoleFilter)
print("MAP: ", mapsdFilter)

plt2 = pg.plot()
plt2.showGrid(x=True, y=True)
plt2.addLegend()
plt2.setWindowTitle("Local Maxima and Minima")
plt2.setLabel('left', 'BloodPreasure', units='mmHg')
plt2.setLabel('bottom', 'Time', units='s')

# Graficar la señal filtrada y los puntos de máximos y mínimos locales
plt2.plot(faxis, newfHP, pen='y', name='Passband Filter')
plt2.plot(faxis[localMax], yMax, pen=None, symbol='o', symbolBrush='g', name='Local Maxima', symbolSize=2)
plt2.plot(faxis[localMin], yMin, pen=None, symbol='o', symbolBrush='r', name='Local Minima', symbolSize=2)


QtGui.QGuiApplication.instance().exec_()