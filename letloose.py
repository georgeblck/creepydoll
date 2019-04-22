# import the necessary packages
from picamera.array import PiRGBArray
from picamera import PiCamera
from utils import *
#from pi_utils import *
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

# make options
min_upload_seconds = 0.1
min_motion_frames = 6
camera_warmup_time = 1
delta_tresh = 5
blur_size = [21, 21]
resolution = [1280, 960]
fps = 20
min_area = 10000
pin = 23

# init GPIO shit
GPIO.setmode(GPIO.BCM)
GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# initialize the camera and grab a reference to the raw camera capture
camera = PiCamera()
camera.resolution = tuple(resolution)
camera.framerate = fps
rawCapture = PiRGBArray(camera, size=tuple(resolution))

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

            # compute the bounding box for the contour, draw it on the frame,
            # and update the text
            (x, y, w, h) = cv2.boundingRect(c)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            text = "Occupied"

        # draw the text and timestamp on the frame
        ts = timestamp.strftime("%A %d %B %Y %I:%M:%S%p")
        cv2.putText(frame, "Room Status: {}".format(text), (10, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        cv2.putText(frame, ts, (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX,
                    0.35, (0, 0, 255), 1)

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
                    play_mp3(make_speech("Du hast mich aufgeweckt. Ich gebe dir 10 Sekunden Zeit um mich zu deaktivieren.",
                                         "de"), 100, round(np.random.uniform(0.4, 2), 3))
                    time.sleep(1)
                    play_mp3(make_speech("Du Ficker.",
                                         "de"), 100, 2)
                    # Listen for spokenword for 10 seconds. Save the recordings!
                    if random.random() >= 0.5:
                        transcribedListen = None
                    else:
                        firstListen = listen_and_interpret(10, "de-DE")
                        transcribedListen = firstListen["transcription"]
                        print(transcribedListen)

                    # If there was speech -> Sleep and exit
                    if transcribedListen != None:
                        print("Sleeping")
                        time.sleep(10)
                    else:
                        # make speech and loudness settings for the path
                        settings = {
                            "path": random.choice(
                                ["button", "parrot_raw", "parrot_recog", "talk_back", "play_sounds"]),
                            "laut": random.randint(90, 100),
                            "schnell": round(np.random.uniform(0.4, 1.7), 3),
                            "lang": random.choice(["de", "en"])
                        }
                        if settings["path"] == "button":
                            # add rising edge detection on a channel
                            GPIO.add_event_detect(pin, GPIO.BOTH)
                            while GPIO.event_detected(pin) == False:
                                button_talk(settings, buttonCounter)
                            buttonCounter += 1
                            play_mp3("creepy_laugh.mp3", 100, 1.8)
                        elif settings["path"] == "play_sounds":
                            chosenSound = random.choice(
                                glob.glob("sounds/*.mp3"))
                            play_mp3(chosenSound)
                        elif settings["path"] == "parrot_raw":
                            mirrorCounter = 0
                            while mirrorCounter < 60 * 1:
                                mirrorLen = random.randint(5, 10)
                                mirrorCounter += mirrorLen
                                listen_and_playback(mirrorLen, settings)
                        elif settings["path"] == "parrot_recog":
                            mirrorCounter = 0
                            while mirrorCounter < 60 * 1:
                                mirrorLen = random.randint(5, 10)
                                mirrorCounter += mirrorLen
                                listen_and_playback(mirrorLen, settings, True)
                        else:
                            print("Not yet implemented")
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
    GPIO.cleanup()
    sys.exit()
