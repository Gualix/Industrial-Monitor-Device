# Industrial Monitor Device

Sistema de monitoreo industrial basado en Raspberry Pi para supervisar
variables críticas en maquinaria o vehículos, con alarmas visuales y
sonoras, almacenamiento histórico y una interfaz gráfica optimizada para
pantalla táctil de 5".

## Características principales

-   Interfaz gráfica moderna y sencilla
-   Compatible con pantalla táctil 5"
-   Horímetro persistente (almacenado en memoria)
-   Alarmas configurables:
    -   Baja presión de aceite (\<10 PSI)
    -   Alta temperatura (\>100 °C)
    -   Recordatorio de mantenimiento cada 500 horas
-   Alarmas sonoras con doble buzzer
-   Inicio automático al encender el Raspberry Pi
-   Arquitectura modular para agregar sensores adicionales

## Hardware requerido

### Microcontrolador

-   Raspberry Pi 3B / 3B+ / 4

### Sensores

-   Sensor de presión de aceite 0--150 PSI (salida 0.5--4.5V)
-   Sensor de temperatura DS18B20 (1-Wire)
-   RTC DS3231 (reloj en tiempo real)
-   ADS1115 (ADC 16 bits I2C)

### Pantalla

-   Pantalla Raspberry Pi 5" táctil

### Alarmas

-   2 Buzzers activos

Conexión:

Buzzer 1 positivo → GPIO 18 negativo → GND

Buzzer 2 positivo → GPIO 23 negativo → GND

### Componentes adicionales

-   Resistencia 4.7kΩ
-   Convertidor DC-DC 12V a 5V
-   Protoboard o PCB
-   Cables Dupont

## Instalación

### 1. Instalar Raspberry Pi OS

https://www.raspberrypi.com/software/

### 2. Actualizar sistema

sudo apt update sudo apt upgrade -y

### 3. Instalar dependencias

sudo apt install python3-pip python3-flask python3-smbus i2c-tools git
-y

pip3 install adafruit-circuitpython-ads1x15 w1thermsensor RPi.GPIO

### 4. Activar interfaces

sudo raspi-config

Activar: - I2C - SPI - 1-Wire

### 5. Clonar repositorio

git clone https://github.com/Gualix/Industrial-Monitor-Device.git

cd Industrial-Monitor-Device

## Ejecución

python3 titanioDashboardApp.py

## Auto inicio

sudo nano /etc/systemd/system/titanio.service

\[Unit\] Description=Industrial Monitor Device After=network.target

\[Service\] ExecStart=/usr/bin/python3
/home/pi/Industrial-Monitor-Device/titanioDashboardApp.py
WorkingDirectory=/home/pi/Industrial-Monitor-Device Restart=always
User=pi

\[Install\] WantedBy=multi-user.target

sudo systemctl daemon-reload sudo systemctl enable titanio.service

## Estructura del proyecto

-   monitor.py
-   monitorv2.py
-   TempSensor.py
-   TestPressureSensor.py
-   buzzer.py
-   titanioDashboardApp.py

## Funcionalidades

### Horímetro

Registra el tiempo total que el equipo ha estado encendido.

### Mantenimiento

Alerta automática cada 500 horas.

### Alarmas

Baja presión: \<10 PSI

Alta temperatura: \>100 °C

Activación sonora mediante doble buzzer conectado a GPIO 18 y GPIO 23.

## Objetivo

Crear un dispositivo confiable y económico para monitoreo de maquinaria
industrial.


## Diagrama general de conexión

### Resumen de conexiones

| Componente | Pin/Señal del módulo | Raspberry Pi |
|---|---|---|
| ADS1115 | VDD | 3.3V o 5V* |
| ADS1115 | GND | GND |
| ADS1115 | SDA | GPIO 2 / SDA (pin físico 3) |
| ADS1115 | SCL | GPIO 3 / SCL (pin físico 5) |
| DS3231 RTC | VCC | 3.3V o 5V* |
| DS3231 RTC | GND | GND |
| DS3231 RTC | SDA | GPIO 2 / SDA (pin físico 3) |
| DS3231 RTC | SCL | GPIO 3 / SCL (pin físico 5) |
| DS18B20 | VCC | 3.3V |
| DS18B20 | GND | GND |
| DS18B20 | DATA | GPIO 4 (pin físico 7) |
| Buzzer 1 activo | Positivo | GPIO 18 (pin físico 12) |
| Buzzer 1 activo | Negativo | GND |
| Buzzer 2 activo | Positivo | GPIO 23 (pin físico 16) |
| Buzzer 2 activo | Negativo | GND |
| Sensor de presión 0–150 PSI | VCC | 5V |
| Sensor de presión 0–150 PSI | GND | GND |
| Sensor de presión 0–150 PSI | Señal analógica | ADS1115 A0 |

\* Verificar el voltaje de operación exacto de cada módulo antes de energizarlo.

### Nota importante para el sensor de presión
El sensor de presión indicado trabaja con salida analógica de **0.5V a 4.5V**.  
Como el Raspberry Pi no puede leer señales analógicas directamente, esa señal entra al **ADS1115**, y luego el ADS1115 envía la lectura por **I2C** al Raspberry Pi.

### Resistencia pull-up para DS18B20
Agregar una resistencia de **4.7kΩ** entre:
- **DATA**
- **3.3V**

### Diagrama de conexión en texto

```text
                           +-----------------------------+
                           |       Raspberry Pi          |
                           |                             |
                           | 3.3V ------------------+----+-----> DS18B20 VCC
                           |                        |    |
                           |                        |    +-----> ADS1115 VDD*
                           |                        |
                           |                        +----------> DS3231 VCC*
                           |
                           | GND -------------------+----------> DS18B20 GND
                           |                        +----------> ADS1115 GND
                           |                        +----------> DS3231 GND
                           |                        +----------> Sensor presión GND
                           |                        +----------> Buzzer 1 negativo
                           |                        +----------> Buzzer 2 negativo
                           |
                           | GPIO 2 / SDA ---------+----------> ADS1115 SDA
                           |                       +----------> DS3231 SDA
                           |
                           | GPIO 3 / SCL ---------+----------> ADS1115 SCL
                           |                       +----------> DS3231 SCL
                           |
                           | GPIO 4 ---------------> DS18B20 DATA
                           |                         |
                           |                         +--[4.7kΩ]---> 3.3V
                           |
                           | GPIO 18 --------------> Buzzer 1 positivo
                           |
                           | GPIO 23 --------------> Buzzer 2 positivo
                           |
                           | 5V --------------------+----------> Sensor presión VCC
                           |
                           +-----------------------------+

       Sensor de presión señal analógica ----------------------> ADS1115 A0
```

### Diagrama lógico simplificado

```text
Sensor de presión ──> ADS1115 ──I2C──> Raspberry Pi
DS3231 RTC        ─────I2C─────> Raspberry Pi
DS18B20           ───1-Wire────> Raspberry Pi
Buzzer 1          ───GPIO 18───> Raspberry Pi
Buzzer 2          ───GPIO 23───> Raspberry Pi
Pantalla táctil 5" ────────────> Raspberry Pi
```

## Archivo requirements.txt

Este proyecto puede usar un archivo `requirements.txt` como referencia para instalar dependencias de Python:

```txt
flask
RPi.GPIO
w1thermsensor
adafruit-circuitpython-ads1x15
adafruit-blinka
```

Instalación:

```bash
pip3 install -r requirements.txt
```
