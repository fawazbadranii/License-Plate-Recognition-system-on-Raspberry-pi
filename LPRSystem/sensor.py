#!/usr/bin/env python3
########################################################################
# Filename    : UltrasonicRanging.py
# Description : Get distance via UltrasonicRanging sensor
# auther      : www.freenove.com
# modification: 2019/12/28
########################################################################
import RPi.GPIO as GPIO
import time
import os
import base64
import requests
import datetime
import threading
import signal
#import main

checkDistance = True
canOpenGate = True
Shutdown = False

from typing import List, Any
from PIL import Image
arr = []
import pymongo
from pymongo import MongoClient
from bson.code import Code

trigPin = 16
echoPin = 18

ledPin = 15    # define ledPin for red light
ledPin2 = 29   # define ledPin for green light
MAX_DISTANCE = 220          # define the maximum measuring distance, unit: cm
timeOut = MAX_DISTANCE*60   # calculate timeout according to the maximum measuring distance

DISTANCE_THRESHOLD = 7     # Distance reached to activate the camera
WAIT_TIME_ON_SUCCESS = 5

windowui = None
############################################################
import sys
import platform
from PySide2 import QtCore, QtGui, QtWidgets
from PySide2.QtCore import (QCoreApplication, QPropertyAnimation, QDate, QDateTime, QMetaObject, QObject, QPoint, QRect, QSize, QTime, QUrl, Qt, QEvent)
from PySide2.QtGui import (QBrush, QColor, QConicalGradient, QCursor, QFont, QFontDatabase, QIcon, QKeySequence, QLinearGradient, QPalette, QPainter, QPixmap, QRadialGradient)
from PySide2.QtWidgets import *
from PyQt5 import QtCore

# GUI FILE
from ui_main import Ui_MainWindow

# IMPORT FUNCTIONS
from ui_functions import *
#######################################

#SERVO MOTOR

OFFSE_DUTY = 0.5        #define pulse offset of servo
SERVO_MIN_DUTY = 2.5+OFFSE_DUTY     #define pulse duty cycle for minimum angle of servo
SERVO_MAX_DUTY = 12.5+OFFSE_DUTY    #define pulse duty cycle for maximum angle of servo
servoPin = 12

def map( value, fromLow, fromHigh, toLow, toHigh):  # map a value from one range to another range
    return (toHigh-toLow)*(value-fromLow) / (fromHigh-fromLow) + toLow

def servoWrite(angle):      # make the servo rotate to specific angle, 0-180 
    if(angle<0):
        angle = 0
    elif(angle > 180): #90
        angle = 180    #90
    dc = SERVO_MIN_DUTY + (SERVO_MAX_DUTY - SERVO_MIN_DUTY) * angle / 180.0 # map the angle to duty cycle
    p.ChangeDutyCycle(dc)
    #p.ChangeDutyCycle(map(angle,0,90,SERVO_MIN_DUTY,SERVO_MAX_DUTY)) # map the angle to duty cycle and output it
############################

def pulseIn(pin,level,timeOut): # obtain pulse time of a pin under timeOut
    t0 = time.time()
    while(GPIO.input(pin) != level):
        if((time.time() - t0) > timeOut*0.000001):
            return 0;
    t0 = time.time()
    while(GPIO.input(pin) == level):
        if((time.time() - t0) > timeOut*0.000001):
            return 0;
    pulseTime = (time.time() - t0)*1000000
    return pulseTime
    
def getSonar():     # get the measurement results of ultrasonic module,with unit: cm
    GPIO.output(trigPin,GPIO.HIGH)      # make trigPin output 10us HIGH level 
    time.sleep(0.00001)     # 10us
    GPIO.output(trigPin,GPIO.LOW) # make trigPin output LOW level 
    pingTime = pulseIn(echoPin,GPIO.HIGH,timeOut)   # read plus time of echoPin
    distance = pingTime * 340.0 / 2.0 / 10000.0     # calculate distance with sound speed 340m/s 
    return distance



def capturePlate():
    print("Detected a car, capturing..")
    time.sleep(1.5)
    os.system("fswebcam testingimage.jpeg -r 1280x720")
    windowui.ui.status_label.setText("Image captured.")
    sendImage()

def sendImage():
    regions = ['gb', 'de'] # Change to your country
    windowui.ui.status_label.setText("Extracting Plate...")
    with open('testingimage.jpeg', 'rb') as fp:
        response = requests.post(
            'https://api.platerecognizer.com/v1/plate-reader/',
            data=dict(regions=regions),  # Optional
            files=dict(upload=fp),
            headers={'Authorization': 'Token 067df8688148ee06e5241ee326a03c110a52194f'})
    results = response.json()[u'results']
    if len(results) > 0:
        windowui.ui.status_label.setText("Plate Extracted")
        print(str(results[0][u'plate']))
        platenumber = str(results[0][u'plate']).upper()
        windowui.ui.licenseplate_label.setText(platenumber)
        checkDB(platenumber)
        time.sleep(WAIT_TIME_ON_SUCCESS)
    else:
        windowui.ui.status_label.setText("Plate Extracted Failed")
        print("No plates detected.")


def resetLabels():
     windowui.ui.status_label.setText("Measuring Distance")
     windowui.ui.name_label.setText("")
     windowui.ui.licenseplate_label.setText("")
     
     
    #reset them all when sensor detects new car

def checkDB(passedplateNumber):
    arr =[]
    print('The passsed Plate number is ' + passedplateNumber)
    #carNumber = passedplateNumber;
    myclient = pymongo.MongoClient("mongodb+srv://mydbAdmin:badguy1996@cluster0.f7c0b.mongodb.net/ALPR?retryWrites=true&w=majority")
    mydb=myclient["ALPR"]
    mycol = mydb["AuthorizedUsers"]
    
    mycol2 = mydb["AuthorizedVehiclesEntered"]
    for x in mycol.find({},{"_id": 0, "LicensePlate": 1 }):
        arr.append((x["LicensePlate"]))
        print(arr) 
    print('CHECKING IF PLATE IS IN THE DATABASE')
    windowui.ui.status_label.setText("Matching Plate with Database!")
    for i in range(len(arr)):
        if arr[i] == passedplateNumber:
            print('Found')
            windowui.ui.status_label.setText("Authorized")
            x = mycol.find_one({"LicensePlate": passedplateNumber}, {"_id": 0}) # we ecluded the id number
            print(x)
            y = x["NameSurname"]
            print(y)
            windowui.ui.name_label.setText(y)
            p =  datetime.datetime.now()
            mycol2.insert_one(x)
            mycol2.update_one(
            {},
            {
                "$currentDate": {
                            "date": { "$type": "timestamp" } #you can also use "timestamp" here or date
                              }
            }, upsert = True
            )
            x= ''
            #global checkDistance  #USE if errors 
            #checkDistance = False
            GPIO.output(ledPin2, GPIO.HIGH)  # make ledPin output HIGH level to turn on led
            rotateMotor()
            #checkDistance = True  
            return
    print('THIS CUSTOMER IS NOT IN THE DATABASE')
    windowui.ui.status_label.setText("Unauthorized")
    GPIO.output(ledPin, GPIO.HIGH)  # make ledPin output HIGH level to turn on led
#    print ('led turned on >>>')     # print information on terminal
    time.sleep(3)                   # Wait for 1 second
    GPIO.output(ledPin, GPIO.LOW)   # make ledPin output LOW level to turn off led

def intializeMotor():
    for dc in range(0, -1, -1): # make servo rotate from 180 to 0 deg
            servoWrite(0)
            

def rotateMotor():
    global canOpenGate
    global checkDistance
    #print(Shutdown)
    if(canOpenGate):
        windowui.ui.gatestatus_label.setText("Opening Gate")
        canOpenGate = False
        time.sleep(1)
        for dc in range(140, 91, -1):   # make servo rotate from 0 to 90 deg181  180 91 
            servoWrite(dc)     # Write dc value to servo
            time.sleep(0.021)  #0.001
        time.sleep(5.5)
        windowui.ui.gatestatus_label.setText("Closing Gate")
        for dc in range(90, 141, 1): # make servo rotate from 90 to 0 deg180   90 181
            servoWrite(dc)
            time.sleep(0.021)
        time.sleep(4.5)
        windowui.ui.gatestatus_label.setText("Closed")
        canOpenGate = True
        windowui.ui.status_label.setText("Thank you for coming")
        print('Thank you For coming')
        GPIO.output(ledPin2, GPIO.LOW)   # make ledPin output LOW level to turn off led
    else:
        print("The gate is already Opened")

def setup():
    GPIO.setmode(GPIO.BOARD)      # use PHYSICAL GPIO Numbering
    GPIO.setup(trigPin, GPIO.OUT)   # set trigPin to OUTPUT mode
    GPIO.setup(echoPin, GPIO.IN)    # set echoPin to INPUT mode
    GPIO.setup(ledPin, GPIO.OUT)   # set the ledPin to OUTPUT mode  for red light
    GPIO.output(ledPin, GPIO.LOW)  # make ledPin output LOW level   for red light
    GPIO.setup(ledPin2, GPIO.OUT)   # set the ledPin to OUTPUT mode  for GREEN light
    GPIO.output(ledPin2, GPIO.LOW)  # make ledPin output LOW level   for GREEN light

    global p
    GPIO.setup(servoPin, GPIO.OUT)   # Set servoPin to OUTPUT mode
    GPIO.output(servoPin, GPIO.LOW)  # Make servoPin output LOW level

    p = GPIO.PWM(servoPin, 50)     # set Frequece to 50Hz
    p.start(0)                     # Set initial Duty Cycle to 0
    

def loop():
        global windowui
        global checkDistance
        #checkDistance=True
        if(checkDistance):
            arr = []
            resetLabels()
            distance = getSonar() # get distance
            distanceValue = "{:.2f}".format(distance)
            windowui.ui.sensor_label.setText(distanceValue)
            if distance < DISTANCE_THRESHOLD and distance != 0.0:
                print('Click')
                capturePlate()
            #time.sleep(1)
        if Shutdown:
            print("Shutting Down Thread")
        elif not Shutdown: #checkDistance and
            threading.Timer(1.0, loop).start()

def destroy():
    p.stop()
    GPIO.cleanup() # release GPIO resource
    sys.exit(0)
    exit()
    
def signal_handler(signal, frame):
    print("exiting")
    sys.exit(0)
  
def defineWindow(window):
    global windowui
    windowui = window

    

if __name__ == '__main__':     # Program entrance
    print ('Program is starting...')
    setup()
    intializeMotor()
#     checkDistance =True
    
    try:
        loop()
    except KeyboardInterrupt:  # Press ctrl-c to end the program.
        destroy()         
        

    
