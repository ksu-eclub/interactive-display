#Kansas State University
#Electronics Design Club
#Interactive Display (Spring Open House, 2019)
#Author(s): Weston Harder

import paho.mqtt.client
import RPi.GPIO as GPIO
import spidev
from time import sleep

#GPIO pin numbers (board #, not BCM #)
CLK = 35
CS_IN = 33
RESET = 37

#SPI global variables
spi = None
#https://pypi.org/project/spidev/
#http://tightdev.net/SpiDev_Doc.pdf
#http://ww1.microchip.com/downloads/en/DeviceDoc/Atmel-9570-AT42-QTouch-BSW-AT42QT1110-Automotive_Datasheet.pdf

def main():
    global CLK
    global CS_IN
    global RESET
    global spi

    #GPIO setup
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(CLK, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(CS_IN, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(RESET, GPIO.OUT, initial=GPIO.HIGH)

    #SPI setup
    spi = spidev.SpiDev()
    spi.open(0, 0) #Not really sure what this should be

    #Both of these come from section 4.1.2: http://ww1.microchip.com/downloads/en/DeviceDoc/Atmel-9570-AT42-QTouch-BSW-AT42QT1110-Automotive_Datasheet.pdf
    spi.max_speed_hz = 14000000 #Max is 1.5 MHz, limit to 1.4 MHz to be safe
    spi.mode = 0b11 # Clock polarity = 1, Clock phase = 1

    tc = touch_controller()
    mqtt_pub = mqtt_publisher()
    
    #Main loop
    while(True):
        #Go through every sensor and check for touch
        tc.scan()

        #Go through each key number
        for key in tc.get_active_keys():
            mqtt_pub.publish_touch(key)

    return

class mqtt_publisher(object):
    def __init__(self):
        self.host = "127.0.0.1"
        self.port = 1883
        self.topic = "interactive_display/touch_events"
        self.mqtt_client = paho.mqtt.client.Client()
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_disconnect = self.on_disconnect
        self.connect()
        self.client.loop_start()
        
        return
    
    def connect(self):
        print("Attempting to connect to \"{}:{}\"".format(self.host, self.port))
        self.client.connect_async(self.host, self.port)
        return

    def on_connect(self, client, userdata, flags, rc):
        if rc==0:
            print("Connected to MQTT server successfully.")
        else:
            print("Failed to connect to the MQTT server. rc = {}".format(rc))
            print("See http://www.steves-internet-guide.com/client-connections-python-mqtt/ or https://pypi.org/project/paho-mqtt/ for help.")
            self.connect()

        return

    def on_disconnect(self, client, userdata, rc):
        print("Disconnected from the MQTT server. rc = {}".format(rc))
        print("See http://www.steves-internet-guide.com/client-connections-python-mqtt/ or https://pypi.org/project/paho-mqtt/ for help.")
        self.connect()

        return

    def publish_touch(self, key):
        rc = self.mqtt_client.publish(self.topic, str(key))

        if rc:
            print("Failed to print message \"{}\" to \"{}\". rc = {}".format(str(key), self.topic, rc))
            print("See https://pypi.org/project/paho-mqtt/ for help.")

        return

class selection_manager(object):
    def __init__(self):
        self.max_touch_ic = 79
        self.touch_ic = self.max_touch_ic + 1

        self.reset()

        return

    def get_max(self):
        return self.max_touch_ic

    def get_number(self):
        return self.max_touch_ic + 1

    def get_selection(self):
        return self.touch_ic

    def increment(self):
        global CLK
        global CS_IN
        global RESET

        #Set CS_IN low
        GPIO.output(CS_IN, GPIO.LOW)
        #Set CLK high
        GPIO.output(CLK, GPIO.HIGH)
        #Wait a few ms???
        #Set CLK low
        GPIO.output(CLK, GPIO.LOW)
        self.touch_ic += 1
        return

    def reset(self):
        global CLK
        global CS_IN
        global RESET

        #Set CS_IN low
        GPIO.output(CS_IN, GPIO.LOW)
        #Set CLK low
        GPIO.output(CLK, GPIO.LOW)
        #Set RESET low
        GPIO.output(RESET, GPIO.LOW)
        #Wait a few ms???
        #Set RESET high
        GPIO.output(RESET, GPIO.HIGH)
        self.touch_ic = self.max_touch_ic + 1
        return

    def select(self, new_touch_ic):
        global CLK
        global CS_IN
        global RESET

        #If selection is valid
        if new_touch_ic >= 0 and new_touch_ic <= self.max_touch_ic:
            #If selection is below current selection
            if new_touch_ic < self.touch_ic:
                #Select touch IC 0
                self.reset()
                #Set CS_IN high
                GPIO.output(CS_IN, GPIO.HIGH)
                #Set CLK high
                GPIO.output(CLK, GPIO.HIGH)
                #Wait a few ms???
                #Set CLK low
                GPIO.output(CLK, GPIO.LOW)
                self.touch_ic = 0

            #While selection is above current selection
            while new_touch_ic > self.touch_ic:
                self.increment()

            return True

        #If selection is invalid
        else:
            self.reset()
            return False


class touch_controller(object):
    def __init__(self):
        self.key_count = 11
        self.key_states = list()
        self.sm = selection_manager()

        #Initialize all keyy states to False
        for _ in range(0, self.get_touch_ic_count()):
            for _ in range(0, self.key_count):
                self.key_states.append(False)

        #Setup all touch ICs
        for i in range(0, self.get_touch_ic_count()):
            self.control_setup(i)
        
        #Calibrate all touch ICs
        for i in range(0, self.get_touch_ic_count()):
            self.control_calibrate(i)

        return
    
    #def get_touch_status()

    def control_calibrate(self, touch_ic):
        global spi

        if self.sm.select(touch_ic):
            #SPI: Send 0x03 to calibrate all keys
            spi.writebytes([0x03])
            
            #Wait at least 150 us before communications can resume
            sleep(150/1000000)

            return True

        else:
            return False

    def control_erase_eeprom_and_reset(self, touch_ic):
        global spi

        if self.sm.select(touch_ic):
            #SPI: Send 0x0c to erase settings stored in EEPROM and reset touch IC (revert touch IC to default settings)
            spi.writebytes([0x0c])
            
            #Wait at least 50 ms before communications can resume
            sleep(50/1000)

            return True

        else:
            return False

    def control_reset(self, touch_ic):
        global spi

        if self.sm.select(touch_ic):
            #SPI: Send 0x04 to reset
            spi.writebytes([0x04])
            
            #Wait at least 160 ms before communications can resume
            sleep(160/1000)

            return True

        else:
            return False

    def control_restore_from_eeprom(self, touch_ic):
        global spi

        if self.sm.select(touch_ic):
            #SPI: Send 0x0b to restore RAM contents from EEPROM (revert to checkpoint without needing to do a full reset)
            spi.writebytes([0x0b])
            
            #Wait at least 150 ms before communications can resume
            sleep(150/1000)

            return True

        else:
            return False

    def control_setup(self, touch_ic):
        global spi

        #Perform initialization on all touch ICs
            #Set the MODE bit in the Device Mode setup
            #Use a timed trigger (specified length of time or 0 for free run mode)
            #No guard channel key
            #No SYNC pin
            #Possibly use detection integrator to make sure it is touched
            #Burst length limitation??? Probably no
            #Adjacent Key Suppression??? Probably no
            #Don't use CRC checking
        
        if self.sm.select(touch_ic):
            #SPI: Send 0x01 to start setup
            spi.writebytes([0x01])
            #SPI: Send 42 bytes of setup data
            spi.writebytes([ #Start in section 7.4: http://ww1.microchip.com/downloads/en/DeviceDoc/Atmel-9570-AT42-QTouch-BSW-AT42QT1110-Automotive_Datasheet.pdf
                0b00000000, #Placeholder 0:  Device Mode
                0b00000000, #Placeholder 1:  Guard Key/Comms Options
                0b00000000, #Placeholder 2:  Detect Integrator Limit (DIL)/Drift Hold Time
                0b00000000, #Placeholder 3:  Positive Threshold (PTHR)/Positive Hysteresis
                0b00000000, #Placeholder 4:  Positive Drift Compensation (PDRIFT)
                0b00000000, #Placeholder 5:  Positive Recalibration Delay (PRD)
                0b00000000, #Placeholder 6:  Lower Burst Limit (LBL)
                0b00000000, #Placeholder 7:  AKS Mask
                0b00000000, #Placeholder 8:  AKS Mask
                0b00000000, #Placeholder 9:  Detect0 PWM
                0b00000000, #Placeholder 10: Detect1 PWM
                0b00000000, #Placeholder 11: Detect2 PWM
                0b00000000, #Placeholder 12: Detect3 PWM
                0b00000000, #Placeholder 13: Detect4 PWM
                0b00000000, #Placeholder 14: Detect5 PWM
                0b00000000, #Placeholder 15: Detect6 PWM
                0b00000000, #Placeholder 16: LED Detect Hold Time
                0b00000000, #Placeholder 17: LED Fade/Key to LED
                0b00000000, #Placeholder 18: LED Latch
                0b00000000, #Placeholder 19: Key 0 Negative Threshold (NTHR) / Negative Hysteresis (NHYST)
                0b00000000, #Placeholder 20: Key 1 Negative Threshold (NTHR) / Negative Hysteresis (NHYST)
                0b00000000, #Placeholder 21: Key 2 Negative Threshold (NTHR) / Negative Hysteresis (NHYST)
                0b00000000, #Placeholder 22: Key 3 Negative Threshold (NTHR) / Negative Hysteresis (NHYST)
                0b00000000, #Placeholder 23: Key 4 Negative Threshold (NTHR) / Negative Hysteresis (NHYST)
                0b00000000, #Placeholder 24: Key 5 Negative Threshold (NTHR) / Negative Hysteresis (NHYST)
                0b00000000, #Placeholder 25: Key 6 Negative Threshold (NTHR) / Negative Hysteresis (NHYST)
                0b00000000, #Placeholder 26: Key 7 Negative Threshold (NTHR) / Negative Hysteresis (NHYST)
                0b00000000, #Placeholder 27: Key 8 Negative Threshold (NTHR) / Negative Hysteresis (NHYST)
                0b00000000, #Placeholder 28: Key 9 Negative Threshold (NTHR) / Negative Hysteresis (NHYST)
                0b00000000, #Placeholder 29: Key 10 Negative Threshold (NTHR) / Negative Hysteresis (NHYST)
                0b00000000, #Placeholder 30: Extend Pulse Time
                0b00000000, #Placeholder 31: Key 0 Negative Drift Compensation (NDRIFT) / Negative Recalibration Delay (NRD)
                0b00000000, #Placeholder 32: Key 1 Negative Drift Compensation (NDRIFT) / Negative Recalibration Delay (NRD)
                0b00000000, #Placeholder 33: Key 2 Negative Drift Compensation (NDRIFT) / Negative Recalibration Delay (NRD)
                0b00000000, #Placeholder 34: Key 3 Negative Drift Compensation (NDRIFT) / Negative Recalibration Delay (NRD)
                0b00000000, #Placeholder 35: Key 4 Negative Drift Compensation (NDRIFT) / Negative Recalibration Delay (NRD)
                0b00000000, #Placeholder 36: Key 5 Negative Drift Compensation (NDRIFT) / Negative Recalibration Delay (NRD)
                0b00000000, #Placeholder 37: Key 6 Negative Drift Compensation (NDRIFT) / Negative Recalibration Delay (NRD)
                0b00000000, #Placeholder 38: Key 7 Negative Drift Compensation (NDRIFT) / Negative Recalibration Delay (NRD)
                0b00000000, #Placeholder 39: Key 8 Negative Drift Compensation (NDRIFT) / Negative Recalibration Delay (NRD)
                0b00000000, #Placeholder 40: Key 9 Negative Drift Compensation (NDRIFT) / Negative Recalibration Delay (NRD)
                0b00000000  #Placeholder 41: Key `0` Negative Drift Compensation (NDRIFT) / Negative Recalibration Delay (NRD)
                ])
            #If concerned about setup working properly:
                #SPI: Request a dump of setup data
                #Check to make sure setup data is correct
            
            #Wait at least 150 us before communications can resume
            sleep(150/1000000)

            return True

        else:
            return False

    def control_sleep(self, touch_ic):
        global spi

        if self.sm.select(touch_ic):
            #SPI: Send 0x05 to sleep
            spi.writebytes([0x05])
            
            #Wait at least 150 us after a low signal is applied to the SS_bar pin before communications can resume
            sleep(150/1000000)

            return True

        else:
            return False

    def control_store_to_eeprom(self, touch_ic):
        global spi

        if self.sm.select(touch_ic):
            #SPI: Send 0x0a to store RAM contents to EEPROM (basically a checkpoint that can be reached again by calling reset)
            spi.writebytes([0x0a])
            
            #Wait at least 200 ms before communications can resume
            sleep(200/1000)

            return True

        else:
            return False

    def get_active_keys(self):
        #Return the indices of all active (touched) keys
        return [index for index, key_state in self.key_states if key_state]

    def get_key_count(self):
        return self.key_count

    def get_key_state(self, key):
        return self.key_states[key]

    def get_touch_ic_key_state(self, touch_ic, key):
        return self.key_states[(touch_ic * self.get_key_count()) + key]

    def get_touch_ic_count(self):
        return self.sm.get_number()
    
    def report_all_keys(self, touch_ic):
        global spi

        if self.sm.select(touch_ic):
            #SPI: Send 0xc1 to request a binary report on all 11 keys
            spi.writebytes([0xc1])

            #SPI: Receive 2 bytes (byte 0 then byte 1)
            response = spi.readbytes(2)

            #           Bit 7   Bit 6   Bit 5   Bit 4   Bit 3   Bit 2   Bit 1   Bit 0
            # Byte 0                                            KEY_10  KEY_9   KEY_8
            # Byte 1    KEY_7   KEY_6   KEY_5   KEY_4   KEY_3   KEY_2   KEY_1   KEY_0
            
            #Parse data and store in self.key_states (For each key, store True if on/triggered and False if off/not triggered)
            touch_ic_key_states = list()
            touch_ic_key_states.append(response[1] & 0b00000001 > 0)
            touch_ic_key_states.append(response[1] & 0b00000010 > 0)
            touch_ic_key_states.append(response[1] & 0b00000100 > 0)
            touch_ic_key_states.append(response[1] & 0b00001000 > 0)
            touch_ic_key_states.append(response[1] & 0b00010000 > 0)
            touch_ic_key_states.append(response[1] & 0b00100000 > 0)
            touch_ic_key_states.append(response[1] & 0b01000000 > 0)
            touch_ic_key_states.append(response[1] & 0b10000000 > 0)
            touch_ic_key_states.append(response[0] & 0b00000001 > 0)
            touch_ic_key_states.append(response[0] & 0b00000010 > 0)
            touch_ic_key_states.append(response[0] & 0b00000100 > 0)

            for i, touch_ic_key_state in enumerate(touch_ic_key_states):
                self.key_states[(touch_ic * self.get_touch_ic_count()) + i] = touch_ic_key_state

            return True

        else:
            return False
    
    def scan(self):
        success = True

        for i in range(0, self.get_touch_ic_count()):
            success = success and self.report_all_keys(i)

        return success

if __name__ == "__main__":
    main()