/*Programa para la lectura y visualizacion de datos analogicos 
a traves del ADS1X15 de 16 bits de resolucion
*/

// Inclusión de bibliotecas necesarias
#include <TFT_eWidget.h>
#include <Adafruit_ADS1X15.h>
#include <TFT_eSPI.h>
#include <SPI.h>
#include "BluetoothSerial.h"

// Definición de pines para los botones
#define BUTTON1PIN 35
#define BUTTON2PIN 0

// Variables para el debounce (anti-rebotes)
const unsigned long debounceDelay = 200;
unsigned long lastDebounceTime = 0, lastChangeTime = 0, lastOnState = 0, lastOffState = 0;
bool lastButtonState = LOW;

// Variables para almacenar el tiempo actual, valor del ADC, voltaje, etc.
float currentTime = 0;
int16_t adcVal;
float volts0;
int i = 0;
float MAX = 0;
float MIN = 0;
int ganancia = 0;
int samplingRate = 0;

float adjust = 0.07;

// Rangos para el gráfico en la pantalla TFT
float gxLow = 0.0;
float gxHigh = 50.0;
float gyLow = -1.0;
float gyHigh = 5.0;



// Objeto para la comunicación Bluetooth
BluetoothSerial SerialBT;
// Objeto para el conversor analógico-digital ADS1115
Adafruit_ADS1115 ads;
// Objeto para la pantalla TFT
TFT_eSPI tft = TFT_eSPI();
// Widget para graficar
GraphWidget gr = GraphWidget(&tft);
// Widget para trazar la línea en el gráfico
TraceWidget tr = TraceWidget(&gr);

#if !defined(CONFIG_BT_ENABLED) || !defined(CONFIG_BLUEDROID_ENABLED)
#error Bluetooth is not enabled! Please run `make menuconfig` to and enable it
#endif

// Función de interrupción para el botón 1
void IRAM_ATTR toggleButton1() {

  bool reading = digitalRead(BUTTON1PIN);
  if (millis() - lastDebounceTime >= debounceDelay) {
    if (reading != lastButtonState) {
      if (millis() - lastChangeTime >= 1000) {
        lastButtonState = reading;
        adjust = 0.01;
        lastChangeTime = millis();
      }
    }
    lastDebounceTime = millis();
  }
}

// Función de interrupción para el botón 2
void IRAM_ATTR toggleButton2() {

  bool reading = digitalRead(BUTTON2PIN);
  if (millis() - lastDebounceTime >= debounceDelay) {
    if (reading != lastButtonState) {
      if (millis() - lastChangeTime >= 1000) {
        lastButtonState = reading;
        adjust = 0.07;
        lastChangeTime = millis();
      }
    }
    lastDebounceTime = millis();
  }
}

void setup(void) {

  // Configuración de pines y de las interrupciones para los botones
  pinMode(BUTTON1PIN, INPUT);
  pinMode(BUTTON2PIN, INPUT);
  attachInterrupt(BUTTON1PIN, toggleButton1, FALLING);
  attachInterrupt(BUTTON2PIN, toggleButton2, FALLING);

  // Inicialización de la comunicación serie y Bluetooth, y de la pantalla TFT
  Serial.begin(115200);
  SerialBT.begin("SinglePointADC");
  tft.begin();
  tft.setRotation(1);
  tft.fillScreen(TFT_BLACK);
  ganancia = 0;

  // Creación y configuración del gráfico en la pantalla TFT
  gr.createGraph(220, 120, tft.color565(5, 5, 5));
  gr.setGraphScale(gxLow, gxHigh, gyLow, gyHigh);
  gr.drawGraph(5, 15);
  tft.setTextSize(1);

  // Configuración del trazado de la línea en el gráfico
  tr.addPoint(0.0, 0.0);
  tr.addPoint(100.0, 0.0);
  tr.startTrace(TFT_GREEN);

  // Inicialización del conversor analógico-digital - Importante para no corromper
  if (!ads.begin()) {
    Serial.println("Failed to initialize ADS.");
    while (1)
      ;
  }


  /*
  #define RATE_ADS1115_8SPS (0x0000)   ///< 8 samples per second
  #define RATE_ADS1115_16SPS (0x0020)  ///< 16 samples per second
  #define RATE_ADS1115_32SPS (0x0040)  ///< 32 samples per second
  #define RATE_ADS1115_64SPS (0x0060)  ///< 64 samples per second (default)
  #define RATE_ADS1115_128SPS (0x0080) ///< 128 samples per second 
  #define RATE_ADS1115_250SPS (0x00A0) ///< 250 samples per second
  #define RATE_ADS1115_475SPS (0x00C0) ///< 475 samples per second
  #define RATE_ADS1115_860SPS (0x00E0) ///< 860 samples per second
  */

  ads.setDataRate(RATE_ADS1115_250SPS);
  ads.getDataRate();
  // Configuración inicial de la ganancia del conversor ADC
  // ads.setGain(GAIN_TWOTHIRDS);  // Ganancia de 2/3x
  ads.setGain(GAIN_ONE);  // Ganancia de 1x   +/- 4.096V  1 bit = 2mV      0.125mV
}

void loop(void) {
  // Variables y constantes estáticas para el bucle principal
  static uint32_t plotTime = millis();
  static float gx = 0.0;
  adcVal = ads.readADC_SingleEnded(0);
  volts0 = ads.computeVolts(adcVal);
  //volts0 += 0.001;

  // Cálculo del tiempo actual y envío de datos por la comunicación serie y Bluetooth
  currentTime = millis() / 1000.0;
  Serial.print(currentTime);
  Serial.print(", ");
  Serial.println(volts0, 5);
  SerialBT.print(currentTime);
  SerialBT.print(", ");
  SerialBT.println(volts0, 5);

  // Impresión en pantalla del valor del voltaje y ajuste del rango del gráfico
  String texto1 = "Val: " + String(volts0) + "Max: " + String(MAX) + " Min: " + String(MIN) + "G: " + String(adjust) + "S: " + String(ads.getDataRate()) ;
  tft.drawString(texto1, 5, 5, 1);
  if (volts0 > MAX) MAX = volts0;
  if (volts0 < MIN) MIN = volts0;

  // Actualización del gráfico
  if (millis() - plotTime >= 50) {
    plotTime = millis();
    tr.addPoint(gx, volts0);
    gx += 1.0;
    if (gx > 50) {
      gx = 0.0;
      gyLow = MIN;
      gyHigh = MAX;
      MIN = MAX;
      MAX = 0;
      volts0 = 0.0;
      gr.drawGraph(5, 15);
      gr.setGraphScale(gxLow, gxHigh, gyLow - (gyLow * adjust), gyHigh + (gyHigh * adjust));
      tr.startTrace(TFT_GREEN);
    }
  }
}
