# Industrial Monitor Device

Backend and frontend separated, ready to run on Raspberry Pi with real sensor reading.

## Hardware used

- Raspberry Pi
- 5-inch touch display
- 2 active buzzers
  - buzzer 1 positive -> GPIO 18
  - buzzer 2 positive -> GPIO 23
  - both negatives -> GND
- DS18B20 temperature sensor
  - data -> GPIO 4
- ADS1115 ADC over I2C
- Pressure sensor 0.5V-4.5V to ADS1115 A0

## Real reading included

- DS18B20 read using `w1thermsensor` and sysfs fallback
- ADS1115 real analog voltage read
- pressure conversion from voltage to PSI
- hourmeter persistence in JSON
- maintenance counter
- alarm logic with both buzzers pulsing together

## Install

```bash
cd scripts
chmod +x install.sh setup_service.sh
./install.sh
```

## Run

```bash
cd backend
source .venv/bin/activate
python run.py
```

Open in browser:

```text
http://localhost:5000
```

## Auto start

```bash
cd scripts
./setup_service.sh
```

## Notes

- ADS1115 is configured with gain 2/3 so it can read up to 6.144V full scale.
- This is suitable for a typical 0.5V to 4.5V pressure sensor.
- If hardware is not detected, safe fallbacks are enabled so the app still starts.
- For production, once validated on your Raspberry Pi, you can disable fallbacks in `backend/app/config.py`.
