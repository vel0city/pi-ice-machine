import RPi.GPIO as GPIO
import Adafruit_DHT
import time
import logging

class IceMaker():
    relays = {
        'water_fill': 12,
        'reverse_cycle': 5,
        'water_circulation': 6,
        'compressor_1': 24,
        'compressor_2': 25,
        'compressor_fan': 23
    }

    sensors = {
        'temp_humid': 17
    }

    fill_count = 0

    def __init__(self):
        self.logger = logging.getLogger()
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        for relay in self.RELAYS.values():
            GPIO.setup(relay, GPIO.OUT, initial=GPIO.HIGH)
            GPIO.output(relay, 1)

    def fill(self):
        # determine how long to fill
        # 2 minutes 
        if self.fill_count >= 50:
            self.fill_count = 0
            sleep_time = 30
        elif self.fill_count == 0:
            self.fill_count += 1
            sleep_time = 240
        else:
            self.fill_count += 1
            sleep_time = 30
        # do the fill
        self.logger.info(f'Filling for {sleep_time} seconds. Fill #{self.fill_count}')
        GPIO.output(self.relays['water_fill'], 0)
        time.sleep(sleep_time)
        GPIO.output(self.relays['water_fill'], 1)

    def freeze(self):
        # Ensure reverse relay is not active
        self.logger.info('Starting to chill.')
        self._start_cool_cycle()

    def circulate(self):
        # Start circulation pump
        self.logger.info('Starting circulation')
        GPIO.output(self.relays['water_circulation'], 0)

    def stop_ice(self):
        self.logger.info('Stopping circulation and compressors.')
        # Stop circulation pump and compressors
        GPIO.output(self.relays['water_circulation'], 1)
        GPIO.output(self.relays['compressor_1'], 1)
        GPIO.output(self.relays['compressor_2'], 1)
        GPIO.output(self.relays['compressor_fan'], 1)

    def remove_ice(self):
        self.logger.info('Removing ice.')
        # Engage reverse cycle, then start compressors again
        # Ensure compressor fan is on
        self._start_heat_cycle()

        # Plate should be warm after 30 seconds of compressor running
        # Turn off compressors
        time.sleep(30)
        self.logger.info('Turning off compressors.')
        GPIO.output(self.relays['compressor_1'], 1)
        GPIO.output(self.relays['compressor_2'], 1)


    def cooldown(self):
        # Ensure compressors are stopped. Leave fan spinning.
        # Cool down for 3 minutes.
        self.logger.info('Starting cooldown mode.')
        GPIO.output(self.relays['compressor_1'], 1)
        GPIO.output(self.relays['compressor_2'], 1)
        GPIO.output(self.relays['compressor_fan'], 0)
        time.sleep(3 * 60)
        GPIO.output(self.relays['compressor_fan'], 1)
        self.logger.info('Leaving cooldown mode.')

    def _start_heat_cycle(self):
        self.logger.info('Starting a heat cycle.')
        # Ensure compressors are off
        GPIO.output(self.relays['compressor_1'], 1)
        GPIO.output(self.relays['compressor_2'], 1)
        time.sleep(5)
        # Ensure reverse cycle is engaged
        GPIO.output(self.relays['reverse_cycle'], 0)
        time.sleep(5)

        # Start compressors
        GPIO.output(self.relays['compressor_fan'], 0)
        GPIO.output(self.relays['compressor_1'], 0)
        GPIO.output(self.relays['compressor_2'], 0)

    def _start_cool_cycle(self):
        self.logger.info('Starting a cool cycle.')
        GPIO.output(self.relays['compressor_1'], 1)
        GPIO.output(self.relays['compressor_2'], 1)
        time.sleep(5)
        # Ensure reverse cycle is not engaged
        GPIO.output(self.relays['reverse_cycle'], 1)
        
        # Start compressors
        time.sleep(5)
        GPIO.output(self.relays['compressor_fan'], 0)
        GPIO.output(self.relays['compressor_1'], 0)
        GPIO.output(self.relays['compressor_2'], 0)


if __name__ is '__main__':
    ice_maker = IceMaker()

    while True:
        ice_maker.fill()
        ice_maker.freeze()
        time.sleep(20)
        ice_maker.circulate()
        time.sleep(15 * 60)
        ice_maker.stop_ice()
        time.sleep(15)
        ice_maker.remove_ice()
        ice_maker.cooldown()
