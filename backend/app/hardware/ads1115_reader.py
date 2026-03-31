def _setup_reader(self) -> None:
    try:
        import board  # type: ignore
        import busio  # type: ignore
        import adafruit_ads1x15.ads1115 as ADS  # type: ignore
        from adafruit_ads1x15.analog_in import AnalogIn  # type: ignore

        i2c = busio.I2C(board.SCL, board.SDA)
        ads = ADS.ADS1115(i2c)
        ads.gain = ADS1115_GAIN

        self.analog_in = AnalogIn(ads, self.channel)

    except Exception:
        import traceback
        print("ADS1115 setup error:")
        traceback.print_exc()
        self.analog_in = None