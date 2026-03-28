import smbus
import time

# dirección I2C del ADS1115
ADS1115_ADDR = 0x48

# registros
REG_CONVERSION = 0x00
REG_CONFIG = 0x01

# configuración:
# canal A0
# +/-4.096V rango
# modo continuo
CONFIG = 0x42C3

bus = smbus.SMBus(1)

def read_voltage():

    # escribir configuración
    bus.write_i2c_block_data(
        ADS1115_ADDR,
        REG_CONFIG,
        [(CONFIG >> 8) & 0xFF, CONFIG & 0xFF]
    )

    time.sleep(0.1)

    # leer conversión
    data = bus.read_i2c_block_data(ADS1115_ADDR, REG_CONVERSION, 2)

    raw_adc = data[0] << 8 | data[1]

    # convertir complemento a 2
    if raw_adc > 32767:
        raw_adc -= 65536

    # convertir a voltaje
    voltage = raw_adc * 4.096 / 32768

    return voltage


print("Leyendo ADS1115 A0...")

while True:

    v = read_voltage()

    print(f"Voltaje: {v:.3f} V")

    time.sleep(1)