# Pi Ice Machine
Raspberry Pi Ice Machine Controller System

This project is to drive an ice maker with a pi, a collection of relays, and a temp/humidity sensor.

# GPIO Definitions
Driving most of this system is a collection of GPIO driven relays and sensors.

## Relays
| Relay Number | Task | Pin ID |
| ------------ | ---- | ------ |
| 1 | Water Fill | 12 |
| 2 | Reverse Cycle | 5 |
| 3 | Water Circiulation Pump | 6 |
| 4 | Compressor 1 | 24 |
| 5 | Compressor 2 | 25 |
| 6 | Compressor Fan | 23 |

## Sensors
| Sensor | Type | Pin ID |
| ------ | ---- | --- |
| Temp/Humid | DHT11 | 17 |


# Standard Cycle Description

MVP of this project is to have a basic cycle process driven based on timers. Advanced cycle concepts will be added after a basic successful run of the maker.

## Step 1 - Fill
Initial run should have the fill stage run for at least 2 minutes. The next 50 runs can run a 30 second fill. After 50 short runs, it should do a long run again to ensure clean flush of fill tank.

## Step 2 - Start Freeze
Ensure reverse cycle relay is off. Five seconds after ensuring reverse is off start the compressors to cool the chill plate. Turn on compressor fan.

## Step 3 - Circulate
20 seconds after compressor starts, enable circulation pump.

## Step 4 - Stop Making Ice
15 minutes after circulation starts, turn off circulation pump and compressors.

## Step 5 - Remove Ice
15 seconds after the ice maker is stopped, engage reverse cycle relay. Five seconds after the reverse relay is engaged enable compressors. This step heats elements inside the ice maker to remove formed ice. Turn off the compressors after 30 seconds. Turn off reverse relay 5 seconds after compressors turn off.

## Step 6 - Cooldown Delay
Let the system rest for 3 minutes before starting over at step 1 again. Turn off fan at end of cooldown.