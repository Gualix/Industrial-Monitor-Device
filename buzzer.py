import RPi.GPIO as GPIO
import time

BUZZER = 18

GPIO.setmode(GPIO.BCM)
GPIO.setup(BUZZER, GPIO.OUT)

try:

    while True:

        GPIO.output(BUZZER, GPIO.HIGH)
        print("Buzzer ON")

        time.sleep(1)

        GPIO.output(BUZZER, GPIO.LOW)
        print("Buzzer OFF")

        time.sleep(1)

except KeyboardInterrupt:

    GPIO.output(BUZZER, GPIO.LOW)
    GPIO.cleanup()
    print("Programa detenido")