from datetime import datetime, time
from gtts import gTTS
import requests
import json
import smtplib
import uuid
import os
import subprocess
import glob

from os.path import basename


class TempImage:
    def __init__(self, basePath="./", ext=".jpg"):
        # construct the file path
        self.path = "{base_path}/{rand}{ext}".format(base_path=basePath,
                                                     rand=str(uuid.uuid4()), ext=ext)

    def cleanup(self):
        # remove the file
        os.remove(self.path)


def playVidwaitButton(mov1, mov2, pin):
    import RPi.GPIO as GPIO
    from subprocess import Popen, PIPE, STDOUT
    import time
    # setup GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    DEVNULL = open(os.devnull, 'wb')
    # Play first video in loop via omxplayer
    omxc = Popen(['omxplayer', '-b', '--loop', mov1],
                 stdin=PIPE, stdout=DEVNULL, stderr=STDOUT)
    while GPIO.input(pin) == GPIO.HIGH:
        time.sleep(0.01)
    # if the button is pressed--> Play the second one
    os.system('killall omxplayer.bin')
    omxc = Popen(['omxplayer', '-b', mov2], stdin=PIPE,
                 stdout=DEVNULL, stderr=STDOUT)
    # Wait for duration of video
    time.sleep(10)
    # And start again from the top
    # playVidwaitButton(mov1, mov2, pin)
    GPIO.cleanup()


def speak(speech, language = "de"):
    filename = 'temp.mp3'
    tts = gTTS(text=speech, lang=language).save(filename)
    play_sound(filename)


def syscmd(cmd):
    from subprocess import Popen, PIPE, STDOUT
    DEVNULL = open(os.devnull, 'wb')
    p = Popen(cmd, shell=True, stdin=PIPE, stdout=DEVNULL, stderr=STDOUT)
    p.wait()


def play_sound(filename, loudness):
    """ Helper function to play audio files in Linux """
    play_cmd = "mplayer -volume {} -speed {} ./{}".format(loudness, 1, filename)
    syscmd(play_cmd)


def is_time_between(begin_time, end_time, check_time=None):
    # If check time is not given, default to current UTC time
    check_time = check_time or datetime.utcnow().time()
    if begin_time < end_time:
        return check_time >= begin_time and check_time <= end_time
    else:  # crosses midnight
        return check_time >= begin_time or check_time <= end_time
