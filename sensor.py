import adafruit_dht
import board
import time
import RPi.GPIO as GPIO
import Adafruit_ADS1x15
import requests
import math
import random
import Adafruit_DHT
import sys
import datetime
import telepot
from picamera import PiCamera
from telepot.loop import MessageLoop
from subprocess import call 

camera = PiCamera()
camera.resolution = (640, 480)
camera.framerate = 25

motion = 0
motionNew = 0

sensor = Adafruit_DHT.DHT11

# sensor variabel
flame=0
temperature=0
humidity=0
gas=0
buzzer_pin=12
GPIO.setmode(GPIO.BCM)
GPIO.setup(buzzer_pin, GPIO.OUT)
import Adafruit_GPIO.SPI as SPI
import Adafruit_SSD1306
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import subprocess

# Raspberry Pi pin configuration:
RST = None     # on the PiOLED this pin isnt used
# Note the following are only used with SPI:
DC = 23
SPI_PORT = 0
SPI_DEVICE = 0
disp = Adafruit_SSD1306.SSD1306_128_64(rst=RST)

# Initialize library.
disp.begin()

# Clear display.
disp.clear()
disp.display()

# Create blank image for drawing.
# Make sure to create image with mode '1' for 1-bit color.
width = disp.width
height = disp.height
image = Image.new('1', (width, height))

# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)

# Draw a black filled box to clear the image.
draw.rectangle((0,0,width,height), outline=0, fill=0)

# Draw some shapes.
# First define some constants to allow easy resizing of shapes.
padding = -2
top = padding
bottom = height-padding
# Move left to right keeping track of the current x position for drawing shapes.
x = 0
# Load default font.
font = ImageFont.load_default()

def led():
    # Draw a black filled box to clear the image.
    draw.rectangle((0,0,width,height), outline=0, fill=0)

    temperature=readDHT()[0]
    humidity=readDHT()[1]
    gas=readGas()
    flame=readFlame()
    # Write two lines of text.
    draw.text((x, top),       "Temp: " + str(temperature),  font=font, fill=255)
    draw.text((x, top+8),     "Humidity: " + str(humidity), font=font, fill=255)
    draw.text((x, top+16),    "Gas: " + str(gas),  font=font, fill=255)
    draw.text((x, top+25),    "Flame: " + str(flame),  font=font, fill=255)

    # Display image.
    disp.image(image)
    disp.display()
    time.sleep(.1)
    
TOKEN = "BBFF-JyLktHIvKBoiCATtbrJ5kO2SqxdjO9"  # Put your TOKEN here
DEVICE_LABEL = "dory"  # Put your device label here 
VARIABLE_LABEL_1 = "temperature"  # Put your first variable label here
VARIABLE_LABEL_2 = "humidity"  # Put your second variable label here
VARIABLE_LABEL_3 = "gas"  # Put your second variable label here
VARIABLE_LABEL_4 = "flame" 

def build_payload(variable_1, variable_2, variable_3, variable_4):
    # Creates two random values for sending data
    value_1 = readDHT()[0]
    value_2 = readDHT()[1]
    value_3 = readGas()
    value_4 = readFlame()
    
    print(value_1)   
    
    global chat_id
    global motion 
    global motionNew
    
    if value_1 > 45:
        print("Terdeteksi Kebakaran")
        alarm()
        motion = 1
        if motionNew != motion:
            motionNew = motion
            sendNotification(motion)
                    
    else:
        print("Tidak Terdeteksi Kebakaran")
        motion = 0
        if motionNew != motion:
            motionNew = motion
            sendNotification(motion)
    payload = {variable_1: value_1,
               variable_2: value_2,
               variable_3: value_3,
               variable_4: value_4,
               }

    return payload


def post_request(payload):
    # Creates the headers for the HTTP requests
    url = "http://industrial.api.ubidots.com"
    url = "{}/api/v1.6/devices/{}".format(url, DEVICE_LABEL)
    headers = {"X-Auth-Token": TOKEN, "Content-Type": "application/json"}

    # Makes the HTTP requests
    status = 400
    attempts = 0
    while status >= 400 and attempts <= 5:
        req = requests.post(url=url, headers=headers, json=payload)
        status = req.status_code
        attempts += 1
        time.sleep(1)

    # Processes results
    print(req.status_code, req.json())
    if status >= 400:
        print("[ERROR] Could not send data after 5 attempts, please check \
            your token credentials and internet connection")
        return False

    print("[INFO] request made properly, your device is updated")
    return True

def main():
    payload = build_payload(VARIABLE_LABEL_1, VARIABLE_LABEL_2, VARIABLE_LABEL_3, VARIABLE_LABEL_4)

    print("[INFO] Attemping to send data")
    post_request(payload)
    print("[INFO] finished")
    
# sensor gas
def readGas():
    adc = Adafruit_ADS1x15.ADS1115()
    GAIN = 1
    gas_pin = 26
    GPIO.setup(gas_pin, GPIO.IN, pull_up_down = GPIO.PUD_OFF)
    deteksiGas = GPIO.input(gas_pin)
    value = adc.read_adc(1, gain=GAIN)
    return value
    #print("Status Gas: {} \t Level Gas: {}".format(deteksiGas, value))
#     return value 
    
def readFlame():
    adc = Adafruit_ADS1x15.ADS1115()
    GAIN = 1
    flame_pin = 21
    GPIO.setup(flame_pin, GPIO.IN, pull_up_down = GPIO.PUD_OFF)
    deteksiFlame = GPIO.input(flame_pin)
    value = adc.read_adc(0, gain=GAIN)
    #print("Status Flame: {}  Level Flame: {}".format(deteksiFlame, value))
    return value

def readDHT():
    #dht = adafruit_dht.DHT11(board.D18, use_pulseio=False)
    #temp = dht.temperature
    #hum = dht.humidity
    #print("Temp: {:.1f} *C \t Humidity: {}%".format(temperature, humidity))pin = 18
    hum, temp = Adafruit_DHT.read_retry(sensor, 18)
    return [temp, hum]

def alarm():
    buzzer = GPIO.PWM(buzzer_pin, 1000) # Set frequency to 1 Khz
    buzzer.start(100) # Set dutycycle to 10

    # this row makes buzzer work for 1 second, then
    # cleanup will free PINS and exit will terminate code execution
    time.sleep(10)
    #GPIO.cleanup()
    
def sendNotification(motion):   
    global chat_id
    if motion == 1:
        filename = "./video_" + (time.strftime("%y%b%d_%H%M%S"))
        camera.start_recording(filename + ".h264")
        sleep(5)
        camera.stop_recording()
        command = "MP4Box -add " + filename + '.h264' + " " + filename + '.mp4'
        print(command)
        call([command], shell=True)
        bot.sendVideo(chat_id, video = open(filename + '.mp4', 'rb'))
        bot.sendMessage(chat_id, 'The motion sensor is')
        

def handle(msg):
    global telegramText
    global chat_id
  
    chat_id = msg['chat']['id']
    telegramText = msg['text']
  
    print('Message received from ' + str(chat_id))
  
    if telegramText == '/start':
        bot.sendMessage(chat_id, 'Security camera is activated.')#Put your welcome note here
bot = telepot.Bot('5643661679:AAGmxdGQ0M37B42Ei0Mkf1XJ6dNISh6ylNE')
bot.message_loop(handle) 

def sendNotification(motion):   
    global chat_id
    if motion == 1:
        filename = "./video_" + (time.strftime("%y%b%d_%H%M%S"))
        camera.start_recording(filename + ".h264")
        time.sleep(5)
        camera.stop_recording()
        command = "MP4Box -add " + filename + '.h264' + " " + filename + '.mp4'
        print(command)
        call([command], shell=True)
        bot.sendVideo(chat_id, video = open(filename + '.mp4', 'rb'))
        bot.sendMessage(chat_id, 'Terjadi kebakaran!')
        
while True:
   # try:
    #alarm()
    led()
    main()
    #except RuntimeError as e:
        # Reading doesn't always work! Just print error and we'll try again
        #print("Reading from DHT failure: ", e.args)
        #error=e.args   
    time.sleep(1)