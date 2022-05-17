from gpiozero import MotionSensor, Button, LED, Buzzer
from picamera import PiCamera
import picamera
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from subprocess import call 
import os
import email.mime.application
import datetime
import smtplib
from time import sleep
import telepot
import sys
from telepot.loop import MessageLoop
import time
import pyrebase

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

firebase = pyrebase.initialize_app(firebaseConfig)
storage = firebase.storage()
database = firebase.database()
pir = MotionSensor(20)
camera = PiCamera()
led = LED(17)
button = Button(16)
buzzer = Buzzer(27)
motion = 0
motionNew = 0

def handle(msg):
    global telegramText
    global chat_id
    global sendPhoto
 
    chat_id = msg['chat']['id']
    telegramText = msg['text']
     
    print('Message received from ' + str(chat_id))
 
    if telegramText == '/start':
        bot.sendMessage(chat_id, 'Start Command Intiated. Interloper PI Detector Activated.')#Put your welcome note here
        main()
        
    elif telegramText == '/photo':
        sendPhoto = True
        bot.sendMessage(chat_id, 'Photo Command Activated.')#Put your welcome note here
        sendPhoto = False
        capture()
        
#    elif telegramText == '/quit':
#        bot.sendMessage(chat_id, 'The Program is now shutdown')#Put your welcome note here
#        exit()
        
    else:
        bot.sendMessage(chat_id, 'Invalid Command.')#Put your welcome note here
        
bot = telepot.Bot('5097835240:AAG69h2cxoc4_aBj8indNiorMChxo3MSbtI')
bot.message_loop(handle) 

from_email_addr = 'fyazikram@gmail.com'
from_email_password = 'fyaz7860'
to_email_addr = 'fyazikram834@gmail.com'

# Photo Command Function
def capture():
    print("Captruing Photo")
    Captured1 = '/home/pi/Desktop/image.png'
    camera.rotation = 180
    camera.capture(Captured1)
    print("Sending Photo to " + str(chat_id))
    bot.sendPhoto(chat_id, photo = open('/home/pi/Desktop/image.png', 'rb'))

#Start Command Function
def main():
    Alarm_state = True
    global chat_id
    global motion 
    global motionNew
    global telegramText
    global sendPhoto
 


    while True:

        if button.is_pressed:
            Alarm_state = True
            print('Alarm ON')
            
        if Alarm_state == True:
            led.on()
            sleep(1)
            if pir.motion_detected:
                print("Motion Detected")
                led.off()
                buzzer.beep()
                sleep(0.2)
                buzzer.off()
                motion = 1
                if motionNew != motion:
                    motionNew = motion
                    sendNotification(motion)
                    dt = time.strftime("%y%b%d_%H%M%S")
                    name = dt+".jpg"
                    camera.capture(name)
                    storage.child(name).put(name)
                    data = {"The Motion was Detected on the: ":dt}
                    database.child("motionsensor").child("Motion Detected Date and Time Stamp").push(data)
                    os.remove(name)
                sleep(0.2)
                #Video record
                camera.resolution = (640,480)
                camera.rotation = 180
                camera.start_recording('alert_video.h264')
                camera.wait_recording(2)
                camera.stop_recording()

                #capture images
                Captured1 = '/home/pi/Desktop/image' + datetime.datetime.now().strftime('%Y-%m-%d%H:%M:%S') + '.png'
                camera.rotation = 180
                camera.capture(Captured1)

                sleep(1)

                #coverting video from .h264 to .mp4
                command = "MP4Box -add alert_video.h264 alert_video.mp4"
                call([command], shell=True)
                print("video converted")


                #Create the Message
                msg = MIMEMultipart()
                msg[ 'Subject'] = 'INTRUDER ALERT..!!'
                msg['From'] = from_email_addr
                msg['To'] = to_email_addr


                # Video attachment
                Captured = '/home/pi/Desktop/alert_video.mp4'
                fp=open(Captured,'rb')
                att = email.mime.application.MIMEApplication(fp.read(),_subtype=".mp4")
                fp.close()
                att.add_header('Content-Disposition','attachment',filename='video' + datetime.datetime.now().strftime('%Y-%m-%d%H:%M:%S') + '.mp4')
                msg.attach(att)
                #Attach the files 
                File = open(Captured1, 'rb')
                img1 = MIMEImage(File.read())
                File.close()
                msg.attach(img1)
                print("attach successful")

                #removing .h264 & .mp4 extra files
                os.remove("/home/pi/Desktop/alert_video.h264")

                #renaming file
                os.rename('alert_video.mp4', datetime.datetime.now().strftime('%Y-%m-%d%H:%M:%S') + '.mp4')

                #send Mail
                server = smtplib.SMTP('smtp.gmail.com', 587)
                server.starttls()
                server.login(from_email_addr, from_email_password)
                server.sendmail(from_email_addr, to_email_addr, msg.as_string())
                server.quit()
                print('Email sent')
                Alarm_state = True
                   
            else:
                print("No motion detected")
                motion = 0
                #bot.sendMessage(chat_id, 'The motion sensor is not triggered!')
                if motionNew != motion:
                    motionNew = motion

def sendNotification(motion): 
 
    global chat_id
 
    if motion == 1:
        filename = "./video_" + (time.strftime("%y%b%d_%H%M%S"))
        camera.start_recording(filename + ".h264")
        sleep(1)
        camera.stop_recording()
        command = "MP4Box -add " + filename + '.h264' + " " + filename + '.mp4'
        print(command)
        call([command], shell=True)
        bot.sendVideo(chat_id, video = open(filename + '.mp4', 'rb'))
        bot.sendMessage(chat_id, 'The motion sensor is triggered!')
        bot.sendMessage(chat_id, str(datetime.datetime.now()))
 
 
 
while 1:
    time.sleep(5)



