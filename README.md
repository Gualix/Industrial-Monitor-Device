# Industrial Monitor Device

Sistema de monitoreo industrial basado en Raspberry Pi para supervisar
variables críticas en maquinaria o vehículos, con alarmas visuales y
sonoras, almacenamiento histórico y una interfaz gráfica optimizada para
pantalla táctil de 3.5".

## Características principales

-   Interfaz gráfica moderna y sencilla
-   Compatible con pantalla táctil 3.5" (480x320)
-   Horímetro persistente (almacenado en memoria)
-   Alarmas configurables:
    -   Baja presión de aceite (\<10 PSI)
    -   Alta temperatura (\>100 °C)
    -   Recordatorio de mantenimiento cada 500 horas
-   Alarma visual y sonora (buzzer)
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
-   Buzzer

### Pantalla

-   Pantalla Raspberry Pi 3.5" SPI táctil (480x320)

### Componentes adicionales

-   Resistencia 4.7kΩ
-   Convertidor DC-DC 12V a 5V
-   Protoboard o PCB
-   Cables Dupont

## Instalación

### 1. Instalar Raspberry Pi OS

Descargar Raspberry Pi Imager: https://www.raspberrypi.com/software/

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

## Objetivo

Crear un dispositivo confiable y económico para monitoreo de maquinaria
industrial.
