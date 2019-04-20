from datetime import datetime, time
from gtts import gTTS
import requests
import json
import smtplib
import uuid
import os
import subprocess
import glob
from string import whitespace
import pyaudio
import wave
from picamera import PiCamera

from os.path import basename


class TempImage:
    def __init__(self, basePath="./", ext=".jpg"):
        # construct the file path
        self.path = "{base_path}/{rand}{ext}".format(base_path=basePath,
                                                     rand=str(uuid.uuid4()), ext=ext)

    def cleanup(self):
        # remove the file
        os.remove(self.path)


def record_audio(length=10):
    FORMAT = pyaudio.paInt16
    CHANNELS = 2
    RATE = 44100
    CHUNK = 1024
    RECORD_SECONDS = length
    WAVE_OUTPUT_FILENAME = "file.wav"
    audio = pyaudio.PyAudio()

    # start Recording input_device_index = 2
    stream = audio.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, input=True,
                        frames_per_buffer=CHUNK)
    print "recording..."
    frames = []

    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)
    print "finished recording"

    # stop Recording
    stream.stop_stream()
    stream.close()
    audio.terminate()

    waveFile = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    waveFile.setnchannels(CHANNELS)
    waveFile.setsampwidth(audio.get_sample_size(FORMAT))
    waveFile.setframerate(RATE)
    waveFile.writeframes(b''.join(frames))
    waveFile.close()
    syscmd('aplay ' + WAVE_OUTPUT_FILENAME)


def record_video(destination):
    filename = os.path.join(
        destination, datetime.now().strftime('%Y-%m-%d_%H.%M.%S.h264'))
    camera.start_preview()
    camera.start_recording(filename)


def finish_video():
    camera.stop_recording()
    camera.stop_preview()


def speak(speech, language="de"):
    filename = 'temp.mp3'
    tts = gTTS(text=speech, lang=language).save(filename)
    play_sound(filename)


def syscmd(cmd):
    from subprocess import Popen, PIPE, STDOUT
    DEVNULL = open(os.devnull, 'wb')
    p = Popen(cmd, shell=True, stdin=PIPE, stdout=DEVNULL, stderr=STDOUT)
    p.wait()


def play_sound(filename, loudness=100):
    """ Helper function to play audio files in Linux """
    play_cmd = "mplayer -volume {} -speed {} ./{}".format(
        loudness, 1, filename)
    syscmd(play_cmd)


def is_time_between(begin_time, end_time, check_time=None):
    # If check time is not given, default to current UTC time
    check_time = check_time or datetime.utcnow().time()
    if begin_time < end_time:
        return check_time >= begin_time and check_time <= end_time
    else:  # crosses midnight
        return check_time >= begin_time or check_time <= end_time


def play_mp3(path):
    subprocess.Popen(['mpg123', '-q', path]).wait()
