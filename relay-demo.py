import RPi.GPIO as GPIO
import Adafruit_DHT
import time


# PINS
relays = [12, 5, 6, 24, 25, 23, 22, 27]
relay1 = 12
relay2 = 5
relay3 = 6
relay4 = 24
relay5 = 25
relay6 = 23
relay7 = 22
relay8 = 27
temp_humid = 17

# SETUP
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
for relay in relays:
    GPIO.setup(relay, GPIO.OUT, initial=GPIO.LOW)
 
while True:
    humidity, temp = Adafruit_DHT.read_retry(Adafruit_DHT.DHT11, temp_humid)
    print(f"Humidity: {humidity}")
    if (humidity > 70):
        output = GPIO.HIGH
    else:
        output= GPIO.LOW
    for relay in relays:
        GPIO.output(relay, output)
    time.sleep(5)    
