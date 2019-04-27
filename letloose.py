# -*- encoding: iso-8859-15 -*-

# import the necessary packages
from picamera.array import PiRGBArray
from picamera import PiCamera
from utils import *
# from pi_utils import *
import argparse
import warnings
import datetime
import json
import time
import cv2
import sys
import os
import random
import glob
import RPi.GPIO as GPIO
import numpy as np
from num2words import num2words
import re as regexp

#


# make options
min_upload_seconds = 0.1
min_motion_frames = 6
camera_warmup_time = 1
delta_tresh = 5
blur_size = [21, 21]
resolution = [1280, 960]
fps = 15
min_area = 10000
pin = 23

# init GPIO shit
GPIO.setmode(GPIO.BCM)
GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(pin, GPIO.BOTH, bouncetime=10000)

# initialize the camera and grab a reference to the raw camera capture
camera = PiCamera()
camera.resolution = tuple(resolution)
camera.framerate = fps
rawCapture = PiRGBArray(camera, size=tuple(resolution))

# while not is_time_between(datetime.time(8, 00), datetime.time(15, 30)):
#    print("Not yet time")
#    time.sleep(60)

# allow the camera to warmup, then initialize the average frame, last
# uploaded timestamp, and frame motion counter
print "[INFO] warming up..."
time.sleep(camera_warmup_time)
avg = None
lastUploaded = datetime.datetime.now()
motionCounter = 0
print('[INFO] talking raspi started !!')

try:
    # capture frames from the camera
    for f in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
        # grab the raw NumPy array representing the image and initialize
        # the timestamp and occupied/unoccupied text
        frame = f.array
        timestamp = datetime.datetime.now()
        text = "Unoccupied"
        buttonCounter = 0

        ######################################################################
        # COMPUTER VISION
        ######################################################################
        # resize the frame, convert it to grayscale, and blur it
        # TODO: resize image here into cmaller sizes
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, tuple(blur_size), 0)

        # if the average frame is None, initialize it
        if avg is None:
            print "[INFO] starting background model..."
            avg = gray.copy().astype("float")
            rawCapture.truncate(0)
            continue

        # accumulate the weighted average between the current frame and
        # previous frames, then compute the difference between the current
        # frame and running average
        frameDelta = cv2.absdiff(gray, cv2.convertScaleAbs(avg))
        cv2.accumulateWeighted(gray, avg, 0.5)

        # threshold the delta image, dilate the thresholded image to fill
        # in holes, then find contours on thresholded image
        thresh = cv2.threshold(frameDelta, delta_tresh, 255,
                               cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)
        im2, cnts, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
                                        cv2.CHAIN_APPROX_SIMPLE)

        # loop over the contours
        for c in cnts:
            # if the contour is too small, ignore it
            if cv2.contourArea(c) < min_area:
                continue
            text = "Occupied"

        ###################################################################################
        # LOGIC
        ###################################################################################

        # check to see if the room is occupied
        if text == "Occupied":
            # save occupied frame
            cv2.imwrite(
                "/tmp/talkingraspi_{}.jpg".format(motionCounter), frame)

            # check to see if enough time has passed between uploads
            if (timestamp - lastUploaded).seconds >= min_upload_seconds:

                # increment the motion counter
                motionCounter += 1

                # check to see if the number of frames with consistent motion is
                # high enough
                if motionCounter >= int(min_motion_frames):
                    print("Motion detected")
                    ambiente = random.choice(
                        glob.glob("ambient/*.mp3"))
                    syscmd("omxplayer --loop -o local --vol -1500 " +
                           ambiente, False)
                    # make random speech settings
                    settings = {
                        "path": random.choice(
                            ["button", "parrot_raw", "parrot_recog", "talk_back", "play_sounds"]),
                        "pitch": random.randint(3, 9)
                    }
                    speak(u"Ja ja ja ja. Ich erkenne ein neues Gesicht. Ein neuer Mensch, ein neuer Freund zum anfassen und umarmen. Sprich das Zauberwort und ich gehe wieder schlafen. Ansonsten müssen wir spielen.",
                          settings["pitch"])
                    # Listen for spokenword for 10 seconds. Save the recordings!
                    # if random.random() >= 0.5:
                    transcribedListen = None
                    # else:
                    firstListen = listen_and_interpret(10)
                    #transcribedListen = firstListen["transcription"]
                    # print(transcribedListen)

                    if transcribedListen is None:
                        transcribedListen = "Nichts"
                    # If there was speech -> Sleep and exit
                    if regexp.search(r'stop|schlaf|aus|halt', transcribedListen):
                        speak(
                            u"Hast du ein Glück. Gute Nacht und auf Bald. In deinen Träumen.", settings["pitch"])
                        time.sleep(10)
                    else:
                        speak(
                            u"Du Stück. Jetzt bin ich wach. Lass uns spielen.", settings["pitch"])
                        settings["path"] = "button"
                        if settings["path"] == "button":
                            speak(
                                "Mein kleines Auge tut so weh. Siehst du was man mit mir gemacht hat?", settings["pitch"])
                            speak(
                                u"Hilf mir bitte. Du bist doch mein Freund. Und ich möchte so gerne angefasst werden. Drück mein Auge.", settings["pitch"])
                            make_speech(num2words(
                                buttonCounter, lang="de") + u" Menschen haben mich schon gedrückt. Streichel mein Auge. Drück mein Auge.")
                            volume = 80
                            pitch = 0
                            while GPIO.event_detected(pin) == False:
                                volume += 5
                                pitch += 2
                                transform_wav("speak.wav", pitch)
                                syscmd(
                                    "mplayer -volume {} -speed {} speak.wav".format(min(volume, 100), 1), True)
                            buttonCounter += 1
                            syscmd(
                                "mplayer -volume 100 -speed 1.7 creepy_laugh.mp3", False)
                            time.sleep(30)
                        elif settings["path"] == "play_sounds":
                            speak(
                                "Psssst. Ich erzähl dir mal eine Geschichte. Sei ganz leise.", settings["pitch"])
                            chosenSound = random.choice(
                                glob.glob("sounds/*.mp3"))
                            play_audio(chosenSound, True)
                            speak(
                                "Ich habe keinen Mund und ich muss schreien!", settings["pitch"])
                            speak("Macht das nicht Spaß?", settings["pitch"])
                        elif settings["path"] == "parrot_raw":
                            speak(
                                "Komm näher näher näher und erzähl mir eine kleine Geschichte. Deine Stimme klingt so schön.", settings["pitch"])
                            speak(
                                "Und vielleicht kannst du mir so auch etwas reden beibringen. Dann wollen sicher noch mehr Menschen mit mir spielen.", settings["pitch"])
                            mirrorCounter = 0
                            while mirrorCounter < 60 * 1:
                                mirrorLen = random.randint(5, 10)
                                mirrorCounter += mirrorLen
                                tempwav = record_wav(
                                    mirrorLen, "record" + datetime.datetime.now().strftime('%Y-%m-%d_%H.%M.%S'))
                                if random.random() >= 0.5:
                                    play_audio(tempwav, pitch)
                                else:
                                    randwav = random.choice(
                                        glob.glob("recordings/*.wav"))
                                    play_audio(randwav, pitch)
                        elif settings["path"] == "parrot_recog":
                            mirrorCounter = 0
                            while mirrorCounter < 60 * 1:
                                mirrorLen = random.randint(5, 10)
                                mirrorCounter += mirrorLen
                                saidthings = listen_and_interpret(mirrorLen)
                                if saidthings is not None:
                                    speak(saidthings, pitch)
                                else:
                                    speak("Sag mal was jetzt.",
                                          settings["pitch"])

                        else:
                            print("Not yet implemented")

                        speak(
                            u"Jetzt gehe ich wieder schlafen für eine Weile. Bleib bei mir und umarme mich.", settings["pitch"])
                        syscmd("killall mplayer")
                        syscmd("killall omxplayer.bin")
                        time.sleep(120)

                    # update the last uploaded timestamp and reset the motion
                    # counter
                    lastUploaded = timestamp
                    motionCounter = 0

        # otherwise, the room is not occupied
        else:
            motionCounter = 0
        # clear the stream in preparation for the next frame
        rawCapture.truncate(0)

except KeyboardInterrupt:
    syscmd("killall mplayer")
    GPIO.cleanup()
    sys.exit()
