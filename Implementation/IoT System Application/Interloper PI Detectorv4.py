# Libraries and API's Imported  
from gpiozero import MotionSensor, Button, LED, Buzzer
from picamera import PiCamera
import picamera
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from subprocess import call 
import os
import RPi.GPIO as GPIO
import email.mime.application
import datetime
import smtplib
from time import sleep
import telepot
import sys
from telepot.loop import MessageLoop
import time
import pyrebase
from twilio.rest import Client


#Twillio Account SID and Token Setup
account_sid = "AC836c1cf4753582fd0c9a125a0b230f4e"
auth_token = "3c82962f494cace9bec24faf46818bdd"

#Firebase Configiration Code to Link to Firebase Project
firebaseConfig = {
    'apiKey': "AIzaSyC0k72cW3c9269zuVHXwVkl2RV5TX_ozZ4",
    'authDomain': "interloper-pi-detector.firebaseapp.com",
    'databaseURL': "https://interloper-pi-detector-default-rtdb.firebaseio.com",
    'projectId': "interloper-pi-detector",
    'storageBucket': "interloper-pi-detector.appspot.com",
    'messagingSenderId': "203002723801",
    'appId': "1:203002723801:web:31a494a6d82ae7a368edc8",
    'measurementId': "G-68NLMPZM6K"    
}

#Intilizate Firebase Database and Firebase Storage
firebase = pyrebase.initialize_app(firebaseConfig)
storage = firebase.storage()
database = firebase.database()

#Created objects to point to the LED, Button, Buzzer, pirSensor sensor and PI Camera.
# For Example when MotionSensor(20) it means that the MotionSensor is connected to GPIO 20
pirSensor = MotionSensor(20)
pirSensorTwo = MotionSensor(26)
camera = PiCamera()
led = LED(17)
button = Button(16)
buzzer = Buzzer(27)

motion = 0
motionChange = 0

def handle(msg):
    global telegramCommandText
    global chat_id
    global sendPhotoCapture
 
    chat_id = msg['chat']['id']
    telegramCommandText = msg['text']
     
    #Displays the ID of the Telegram Bot Command
    print('Message received from ' + str(chat_id))

    #If the /start is typed on the telegram bot it starts the motion detection system
    if telegramCommandText == '/start':
        #Message Displayed to the Telegram Bot 
        bot.sendMessage(chat_id, 'Start Command Intiated. Interloper PI Detector Activated.')
        #Method to detect motion in the house
        main()
        
    #If the /photo is typed on the telegram bot it captures a photo
    elif telegramCommandText == '/photo':
        sendPhotoCapture = True
        #Message Displayed to the Telegram Bot 
        bot.sendMessage(chat_id, 'Photo Command Activated.')
        sendPhotoCapture = False
        #Method to capture photo from the camera
        capture()
        
    #If the /quit is typed on the telegram bot it quits the program
    elif telegramCommandText == '/quit':
        #Message Displayed to the Telegram Bot 
        bot.sendMessage(chat_id, 'The Program is now shutdown')
        #Exits the Program
        sys.exit()
        
    #If the user types another string on the telegram bot it sends a message saying invalid command.    
    else:
        bot.sendMessage(chat_id, 'Invalid Command.')

#Telegram Bot Account Token Setup
bot = telepot.Bot('5097835240:AAG69h2cxoc4_aBj8indNiorMChxo3MSbtI')
bot.message_loop(handle) 

#Email contact details of sender and reciver
from_email_addr = 'fyazikram@gmail.com'
from_email_password = 'fyaz7860'
to_email_addr = 'fyazikram834@gmail.com'

#Method to capture photo and send to the Telegram Bot (/photo Command Function)
def capture():
    print("Captruing Photo")
    #Stores the image locally first in the desktop directory
    photoCaptured1 = '/home/pi/Desktop/image.png'
    #Camera rotation to 180 degrees
    camera.rotation = 180
    #Captures image 
    camera.capture(photoCaptured1)
    print("Sending Photo to " + str(chat_id))
    #Sends Photo capture to the Telegram Bot 
    bot.sendPhoto(chat_id, photo = open('/home/pi/Desktop/image.png', 'rb'))

#Method to start the motion detetction(/start Command Function)
def main():
    #Intialized all the variables and set the Alarm state to True
    AlarmState = True
    global chat_id
    global motion 
    global motionChange
    global telegramCommandText
    global sendPhotoCapture
    
    try:
        #While the Command is True
        while True:
            #If Alarm State is True, LED is off and waits execution of the current thread for 1 second
            if AlarmState == True:
                led.off()
                sleep(1)
                #If motion is detected from either of the 2 sensors a message would be displayed that there has been motion detetced and turns on the LED and Beeps
                if pirSensor.motion_detected or pirSensorTwo.motion_detected:
                    print("Motion Detected")
                    led.on()
                    buzzer.beep()
                    #Waits execution of the current thread for a 0.2 seconds
                    sleep(0.2)
                    #Then after that turns off the buzzer
                    buzzer.off()
                    #Waits for 10 seconds for user to push button 
                    button.wait_for_press(timeout=10)
                    
                    #If button is pressed within 10 seconds the program exits and turns off the LED
                    if button.is_pressed:
                        print("\nThe System Has Been Exited!")
                        bot.sendMessage(chat_id, 'The System Has Been Exited!')
                        led.off()
                        sys.exit()
                        
                    #If button is NOT pressed within 10 seconds the program continues
                    else:
                        print("\nThere is an Intruder in your house!")
                        #Sends a message to the Telegram Bot that there is an intruder in your house, and displays a message that a message is going to be sent to the Garda Station
                        bot.sendMessage(chat_id, 'There is an Intruder in your house!')
                        bot.sendMessage(chat_id, 'Messaging the Local Garda Station')
                        #Collecting the Account SID and Authentication Token from the Twillio Bot
                        client = Client(account_sid, auth_token)
                        #Twillio bot sends a message to the Garda that the house has been intruded, with their address.
                        message = client.api.account.messages.create(to="+353894389623",from_="+15599920648",body="Dear Sir/Madam, There has beeen an intrusion in my house. My address is 25 The Crescent, Kilteragh, Dooradoyle, Limerick. (V94FDN8)")
                        #Sets the motion to 1 from 0 to show that motion has been detected.
                        motion = 1
                        
                        #If motion=1 and motionChange=0 
                        if motionChange != motion:
                            #Sets the motionChange = motion 
                            motionChange = motion
                            #Calls the sendNotification method and passes the motion argument 
                            sendNotification(motion)
                            dt = time.strftime("%y-%b-%d_%H:%M:%S")
                            #Sets the file with the date as the name and the extension which is .jpg photo format
                            name = dt+".jpg"
                            #Sets the camera resolution to 640x480
                            camera.resolution = (640,480)
                            #Sets the camera rotation to 180 degrees
                            camera.rotation = 180
                            #Captures the photo with the name of the file
                            camera.capture(name)
                            #Saves and stores the photo capture to Firebase Storage
                            storage.child(name).put(name)
                            #Saves and stores the date and timestamps to the Firebase Realtime Database
                            data = {"sensorTriggered":dt}
                            database.child("sensorTriggered").push(data)
                            #Deletes and removes the file path
                            os.remove(name)
                            
                        #Waits execution of the current thread for a 0.2 seconds
                        sleep(0.2)
                        #Recording a video with the .h264 extension
                        #Set the camera resolution to 640x480
                        camera.resolution = (640,480)
                        #Set the camera rotation to 180 degrees
                        camera.rotation = 180
                        #Start the camera recording using the filename created and with the .h264 extension to record video as raspberry pi uses the default .h264 extension to record videos
                        camera.start_recording('alert_video.h264')
                        #Records the video for 20 seconds
                        camera.wait_recording(20)
                        #After 20 seconds the camera stops recording
                        camera.stop_recording()
                        #Captures images and stores it locally first on the Desktop and sets the file name as the date and timestamp with the .png extension for photos
                        photoCaptured1 = '/home/pi/Desktop/image' + datetime.datetime.now().strftime('%Y-%m-%d%H:%M:%S') + '.png'
                        #Set the camera resolution to 640x480
                        camera.resolution = (640,480)
                        #Set the camera rotation to 180 degrees
                        camera.rotation = 180
                        #Captures the image
                        camera.capture(photoCaptured1)
                        #Waits execution of the current thread for 1 second
                        sleep(1)
                        
                        #Converts the video from .h264 extension to the .mp4 video extension
                        command = "MP4Box -add alert_video.h264 alert_video.mp4"
                        call([command], shell=True)
                        print("video converted")
                        
                        #Creating the Email Message with the Subject, Body, From Sender and To Sender Data, with MIMEMultipart library.
                        msg = MIMEMultipart()
                        msg[ 'Subject'] = 'Motion Sensor Triggered. Email Alert'
                        msg[ 'Body'] = 'Hi Fyaz, There has been an Intruder in your house. I have attached a photo & video of when the motion sensor was triggered, please have a look, Many Thanks'
                        msg['From'] = from_email_addr
                        msg['To'] = to_email_addr
                        
                        #Creating a video attachment to send with the email message
                        videoCaptured1 = '/home/pi/Desktop/alert_video.mp4'
                        fp=open(videoCaptured1,'rb')
                        att = email.mime.application.MIMEApplication(fp.read(),_subtype=".mp4")
                        fp.close()
                        att.add_header('Content-Disposition','attachment',filename='video' + datetime.datetime.now().strftime('%Y-%m-%d%H:%M:%S') + '.mp4')
                        msg.attach(att)
                        
                        #Creating a photo attachment to send with the email message 
                        File = open(photoCaptured1, 'rb')
                        img1 = MIMEImage(File.read())
                        File.close()
                        msg.attach(img1)
                        
                        #Message to confirm that the files have been sucesfully attached
                        print("attach successful")
                        #removing .h264 & .mp4 extra files
                        os.remove("/home/pi/Desktop/alert_video.h264")
                        #renaming file
                        os.rename('alert_video.mp4', datetime.datetime.now().strftime('%Y-%m-%d%H:%M:%S') + '.mp4')
                        
                        #Sending the email to the speciifed address with the nessecary configuartions
                        server = smtplib.SMTP('smtp.gmail.com', 587)
                        server.starttls()
                        server.login(from_email_addr, from_email_password)
                        server.sendmail(from_email_addr, to_email_addr, msg.as_string())
                        server.quit()
                        
                        #Message to confirm that the email has been sucesfully sent
                        print('Email sent')
                        #Sets the Alarm State to True again to continue montoring motion
                        AlarmState = True
                        
                else:
                    #If no motion is detected motion is = 0
                    print("No motion detected")
                    motion = 0
                    #bot.sendMessage(chat_id, 'The motion sensor is not triggered!')
                    if motionChange != motion:
                        motionChange = motion                     
    except KeyboardInterrupt:
        print("\nApplication stopped!")

#Method to send notification to the Telegram Bot that a motion has beeen detected
def sendNotification(motion): 
     
    #Intiliazing the global Telegram Bot Chat ID
    global chat_id
 
    #If the motion = 1
    if motion == 1:
        #Creates a filename with the datetime timestamp as the file name
        filename = "./video_" + (time.strftime("%y%b%d_%H%M%S"))
        #Set the camera resoltion to 640x480
        camera.resolution = (640,480)
        #Sets the camera resolution to 180 degrees
        camera.rotation = 180
        #Start the camera recording using the filename created and with the .h264 extension to record video as raspberry pi uses the default .h264 extension to record videos
        camera.start_recording(filename + ".h264")
        #Waits execution of the current thread for 1 second
        sleep(1)
        #Records video for 20 seconds
        camera.wait_recording(20)
        #finishes recording after 20 seconds.
        camera.stop_recording()
        #Splits and creates an individual playable video file (.mp4) from the original (.h624) video extension
        command = "MP4Box -add " + filename + '.h264' + " " + filename + '.mp4'
        print(command)
        
        #Converts the video from .h264 extension to the .mp4 video extension
        call([command], shell=True)
        bot.sendVideo(chat_id, video = open(filename + '.mp4', 'rb'))
        bot.sendMessage(chat_id, 'The motion sensor is triggered!')
        bot.sendMessage(chat_id, str(datetime.datetime.now()))

