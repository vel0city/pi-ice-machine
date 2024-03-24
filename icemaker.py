import RPi.GPIO as GPIO
import adafruit_dht
import time
import datetime
import board
import logging
import sys
from w1thermsensor import W1ThermSensor, Unit

# 0 indicates active relay
# 1 indicates inactive relay

class IceMaker():

    
    relays = {
        # water pump to fill the resevoir
        'water_valve': 12,
        # melts the ice from the plate
        'hot_gas_solenoid': 5,
        # builds ice on the plate
        'recirculating_pump': 6,
        # main compressor, reverse relay cannot active when compressors are ON
            # needs to be tuned into function
        'compressor_1': 24,
        # main compressor, reverse relay cannot active when compressors are ON
            # needs to be tuned into function
        'compressor_2': 25,
        # Needs to be on when running an ice making cycle
            # when the compressor is on and the reverse relay is off (ice making cylce)
        'condenser_fan': 23,
        # LED light for status of ice machine
        'LED': 22,
        # Ice Cutter
        'ice_cutter': 27
    }
    
    relay_names = {
        # water pump to fill the resevoir
        'water_valve': 'Water Valve',
        # melts the ice from the plate
        'hot_gas_solenoid': 'Hot Gas Solenoid',
        # builds ice on the plate
        'recirculating_pump': 'Recirculating Pump',
        # main compressor, reverse relay cannot active when compressors are ON
            # needs to be tuned into function
        'compressor_1': 'Compressor 1',
        # main compressor, reverse relay cannot active when compressors are ON
            # needs to be tuned into function
        'compressor_2': 'Compressor 2',
        # Needs to be on when running an ice making cycle
            # when the compressor is on and the reverse relay is off (ice making cylce)
        'condenser_fan': 'Condenser Fan',
        # LED light for status of ice machine
        'LED': 'LED',
        # Ice Cutter
        'ice_cutter': 'Ice Cutter'
    }

    #sensors = {
    #     # Whole machine temperature and humidity sensor
    #    'temp_humidity_sensor': 17
    #}

    # fill counters
    fill_count = 0
    total_fill_count = 0
    MIN=60

    def __init__(self):
        #self.MIN = 2 if self.debug else 60
        logging.basicConfig(stream=sys.stdout, 
                level=logging.DEBUG,
                format='%(asctime)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S')
        self.logger = logging.getLogger()
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        for relay in self.relays.values():
            GPIO.setup(relay, GPIO.OUT, initial=GPIO.HIGH)
            GPIO.output(relay, 1)
        
        # Setup 1-Wire temp sensors
        self.ice_bin_temp_sensor_id = "3c01f0956abd"
        self.plate_temp_sensor_id = "092101487373"
        self.ice_bin_temp_sensor = W1ThermSensor(sensor_id=self.ice_bin_temp_sensor_id)
        self.plate_temp_sensor = W1ThermSensor(sensor_id=self.plate_temp_sensor_id)

    def sensor_check(self):
        try:
            #ambient_th_sensor = adafruit_dht.DHT22(board.D17, False)
            #ice_bucket_temp = W1ThermSensor()

            #temperature_c = ambient_th_sensor.temperature
            #temperature_f = temperature_c * (9 / 5) + 32
            #humidity = ambient_th_sensor.humidity
            ice_bucket_temperature = ice_bucket_temp.get_temperature()
            ice_bucket_temperature_f = ice_bucket_temperature * (9 / 5) + 32
            #print("Temp={0:0.1f}ºC, Temp={1:0.1f}ºF, Humidity={2:0.1f}%, Temp={3:0.1f}ºF".format(temperature_c, temperature_f, humidity, ice_bucket_temperature))
            self.logger.info("Ice Bucket Temp={0:0.1f}ºF".format(ice_bucket_temperature_f))
            return ice_bucket_temperature_f
        except RuntimeError as error:
            # Errors happen fairly often, DHT's are hard to read, just keep going
            print(error.args[0])
            return None
        except Exception as error:
            ambient_th_sensor.exit()
            return None

    def power_off(self):
        for relay in self.relays.keys():
            print(relay)
            self.relay_off(relay)
        self.logger.warning('Powered off all relays.')

    def power_on(self):
        #start up only, aka only one run once on first boot
        self.logger.info('\tActivating Power On Startup Sequence')

        # turn on the water valve for 2 minutes
        duration = 0.25
        self.logger.info(f'\t\tTurning on water valve for {duration} min.')
        self.relay_on('water_valve')
        time.sleep(duration * self.MIN)
        # turn off the water valve
        self.logger.info('\t\tTurning off water valve')
        self.relay_off('water_valve')

        # turn on the recirculating pump for 1 minute
        duration = 0.25
        self.logger.info(f'\t\tTurning on recirculating pump for {duration} min.')
        self.relay_on('recirculating_pump')
        time.sleep(duration * self.MIN)
        # turn off the recirculating pump 
        self.logger.info('\t\tTurning off recirculating pump')
        self.relay_off('recirculating_pump')

        # turn on the water valve for 2 minutes
        duration = 0.25
        self.logger.info(f'\t\tTurning on water valve for another {duration} min.')
        self.relay_on('water_valve')
        time.sleep(duration * self.MIN)
        # turn off the water valve
        self.logger.info('\t\tTurning off water valve')
        self.relay_off('water_valve')

        #completion of power on sequence
        self.logger.info('\tCompletion of Power On Sequence')  
        
    def chill_plate(self, timeout=25*60, target_temp=25, recirc=False):
        start_time = time.monotonic()
        self.logger.info(f'\tChilling Plate to {target_temp} °F')
        temp = self.plate_temp_sensor.get_temperature(Unit.DEGREES_F)
        bin_temp = self.ice_bin_temp_sensor.get_temperature(Unit.DEGREES_F)
        
        chilling = True if (temp > target_temp) else False # Only turn compressor etc on if temp is above target temp
        if chilling:
            # hot gas/water fill OFF
            self.relay_off('hot_gas_solenoid', True)
            self.relay_off('water_valve', True)
            # condenser/compressor ON
            self.relay_on('condenser_fan', True)
            self.relay_on('compressor_1', True)
            self.relay_on('compressor_2', True)
            # recirculating pump
            if recirc:
                self.relay_on('recirculating_pump', True)
            else:
                self.relay_off('recirculating_pump', True)
        else:
            self.logger.info(f'\tSkipping Chilling Sequence.  Plate temp ({temp} °F) is below target temp ({target_temp} °F).')
        
        wait_time = self.MIN / 12
        while chilling:
            temp = self.plate_temp_sensor.get_temperature(Unit.DEGREES_F) 
            bin_temp = self.ice_bin_temp_sensor.get_temperature(Unit.DEGREES_F)
            time_spent = time.monotonic() - start_time
            if time_spent > timeout: # Check for timeout
                chilling = False
                self.logger.info(f'\tChilling Timed out after {timeout/60} minutes.  Ending Chilling Sequence.')
            elif temp > target_temp:  # Continue Chilling Plate if still above target temp
                # wait for plate temp to reach > 52 degrees F
                self.logger.info(f'Target: {target_temp} °F. Current Temp: {temp:.2f} °F Plate, {bin_temp:.2f} °F Bin.  Time spent: {time_spent/60:.02f} minutes')
                time.sleep(wait_time)
            else:  # stop if reached target temp
                self.logger.info(f'\Current Temp: {temp:.2f} °F.  Reached chilling target ({target_temp} °F)!')
                chilling = False
                self.logger.info('\tEnding Chilling Sequence')
        #  Condenser fan & compressor are left ON.  Main loop decides what to do based on ice bin fullness (proceed to ice making or go to sleep)
              
        
    def ice_making(self, ice_target_temp = 6.5):
        #Start ice making sequence
        self.logger.info('\tActivating Ice Making Sequence')

        # PRECHILL ICE PLATE
        #self.chill_plate(timeout= 2*self.MIN)
        
        # Ice-making phase
        self.logger.info('\t\tStarting Ice Making Process')
        self.chill_plate(target_temp=ice_target_temp, recirc=True, timeout=25*self.MIN)
        self.logger.info('\t\tCompleting Ice Making Process')
        # Finish Ice-Making Phase
        #   Turn off condenser fan & recirc pump, but leave compressor on (for harvest)
        self.relay_off('condenser_fan',True)
        self.relay_off('recirculating_pump',True)
        self.logger.info('\tCompleting Ice Making Sequence')

    def harvest(self, timeout = 4*60, harvest_threshold = 52.5):
        start_time = time.monotonic()
        self.logger.info(f'\Activating Harvest Sequence.  Target temp: {harvest_threshold} °F')
        #Start harvest sequence
        # ensure condenser fan & recirc pump are off
        self.relay_off('condenser_fan')
        self.relay_off('recirculating_pump')
        
        # start harvest
        self.relay_on('water_valve', True)  # Fill water reservoir while harvesting
        self.relay_on('hot_gas_solenoid', True) # Configure to heat the plate
        self.relay_on('ice_cutter') # Turn on ice cutter
        harvesting = True
        wait_time = self.MIN / 12
        while harvesting:
            temp = self.plate_temp_sensor.get_temperature(Unit.DEGREES_F)
            if (time.monotonic() - start_time) > timeout: # Check for timeout
                harvesting = False
                self.logger.info(f'\tHarvest Timed out after {timeout/60} minutes')
            elif temp < harvest_threshold:
                # wait for plate temp to reach > 52 degrees F
                self.logger.info(f'\Waiting  ({wait_time} more seconds) for plate to warm up to {harvest_threshold} °F. Current Temp: {temp:.2f} °F')
                time.sleep(wait_time)
            else:
                self.logger.info(f'\tCurrent Temp: {temp:.2f} °F.  Reached harvest threshold ({harvest_threshold} °F)!')
                harvesting = False

            # end harvest
        self.logger.info('\tEnding Harvest Sequence')
        self.relay_off('hot_gas_solenoid', True)
        self.relay_off('water_valve', True)
        # leave compressor on (prep for cooling off the plate), turn on condenser fan
        self.relay_on('condenser_fan', True)

    def test_relay(self, relay, duration):
        self.logger.info('\tRelay Test')
        self.relay_on(relay, True)
        time.sleep(duration)
        self.relay_off(relay, True)

    def relay_on(self, relay, log = False):
        if log:
            self.logger.info(f'\t\tTurning ON {self.relay_names[relay]}')
        GPIO.output(self.relays[relay], 0)

    def relay_off(self, relay, log = False):
        if log:
            self.logger.info(f'\t\tTurning OFF {self.relay_names[relay]}')
        GPIO.output(self.relays[relay], 1)
    def bin_full(self, threshold=35):
        bucket_temp = self.ice_bin_temp_sensor.get_temperature(Unit.DEGREES_F)
        ice_maker.logger.info(f'Bucket temp: {bucket_temp} °F.')
        return (bucket_temp < threshold)
        
if __name__ == '__main__':
    ice_maker = IceMaker()
    ice_maker.debug = False
    ice_maker.MIN = 60
    
    # Debug Only ------------------
    if ice_maker.debug:
        ice_maker.MIN = 60
        # walk through relays 1 at a time
        test_time = 10 #seconds
        for relay in ['water_valve', 'condenser_fan', 'recirculating_pump', 'hot_gas_solenoid', 'ice_cutter']:
            ice_maker.test_relay(relay, test_time)
        # Turn on/off compressor_1 & _2 together
        ice_maker.relay_on('compressor_1', True)
        ice_maker.relay_on('compressor_2', True)
        time.sleep(test_time)
        ice_maker.relay_off('compressor_1', True)
        ice_maker.relay_off('compressor_2', True)
    # -----------------------------       
    
    try:
        for sensor in W1ThermSensor.get_available_sensors():
            ice_maker.logger.info("Sensor %s has temperature %.2f deg C" % (sensor.id, sensor.get_temperature()))
            ice_maker.logger.info("Sensor %s has temperature %.2f deg F" % (sensor.id, sensor.get_temperature(Unit.DEGREES_F)))
    except:
        ice_maker.logger.error('Error reading temperature sensor on startup.')
            
    ice_maker.logger.info('Powering On...')
    try:
        ice_maker.power_on()
        while True:
            ice_maker.relay_on('ice_cutter') # Turn on ice cutter
            
            ice_maker.chill_plate(timeout=2*ice_maker.MIN, target_temp=25)  #       Prechill
            ice_maker.ice_making(ice_target_temp=-2) #                             Make Ice
            ice_maker.harvest(timeout=4*ice_maker.MIN, harvest_threshold=36) #    Harvest
            ice_maker.chill_plate(timeout=5*ice_maker.MIN, target_temp=30) #        Rechill
            cycle_finish_time = time.monotonic()
            while ice_maker.bin_full():
                ice_maker.logger.info(f'Ice bin full...sleeping.')
                time.sleep(1 * ice_maker.MIN)
                if time.monotonic() > (cycle_finish_time + 15*ice_maker.MIN):
                    #ice_maker.relay_off('ice_cutter')
                    pass
                    
            ice_maker.logger.info(f'Ice Bin not full...restarting ice-making cycle.')

    except:
        ice_maker.logger.warning('SYSTEM POWER OFF, TURNING OFF ALL RELAYS...')
        ice_maker.power_off()
