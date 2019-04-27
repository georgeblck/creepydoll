# -*- encoding: iso-8859-15 -*-

import os
import subprocess
import glob
import uuid
import pyaudio
import wave
import datetime
import random
import speech_recognition as sr
import numpy as np
import librosa
from num2words import num2words
from gtts import gTTS


class TempImage:
    def __init__(self, basePath="./", ext=".jpg"):
        # construct the file path
        self.path = "{base_path}/{rand}{ext}".format(base_path=basePath,
                                                     rand=str(uuid.uuid4()), ext=ext)

    def cleanup(self):
        # remove the file
        os.remove(self.path)


def syscmd(cmd, waiting=True):
    DEVNULL = open(os.devnull, 'wb')
    p = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE,
                         stdout=DEVNULL, stderr=subprocess.STDOUT)
    if waiting == True:
        p.wait()


def record_wav(length, filename, chan=1, rat=11000, chk=256):
    FORMAT = pyaudio.paInt16
    CHANNELS = chan  # 1
    RATE = rat  # 11000
    CHUNK = chk  # 1024
    RECORD_SECONDS = length
    WAVE_OUTPUT_FILENAME = "recordings/" + filename + ".wav"
    audio = pyaudio.PyAudio()
    print(WAVE_OUTPUT_FILENAME)
    # start Recording
    stream = audio.open(format=FORMAT, channels=CHANNELS, input_device_index=0,
                        rate=RATE, input=True,
                        frames_per_buffer=CHUNK)
    print "recording..."
    frames = []

    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)
    print "finished recording"

    # stop Recording
    # stream.stop_stream()
    stream.close()
    # audio.terminate()

    waveFile = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    waveFile.setnchannels(CHANNELS)
    waveFile.setsampwidth(audio.get_sample_size(FORMAT))
    waveFile.setframerate(RATE)
    waveFile.writeframes(b''.join(frames))
    waveFile.close()
    return WAVE_OUTPUT_FILENAME


def interpret_wav(wavname, recognizer, lang="de-DE"):
    if not isinstance(recognizer, sr.Recognizer):
        raise TypeError("`recognizer` must be `Recognizer` instance")

    wavSource = sr.AudioFile(wavname)
    with wavSource as source:
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.record(source)

    # set up the response object
    response = {
        "success": True,
        "error": None,
        "transcription": None
    }

    # try recognizing the speech in the recording
    # if a RequestError or UnknownValueError exception is caught,
    #     update the response object accordingly
    try:
        # response["transcription"] = recognizer.recognize_google(
            # audio, language=lang)
        azKey = random.choice(
            ["929ceac53b6144b98bf2bcec94077198", "e887f21dfd9649f5a2264f2540990de3"])
        response["transcription"] = recognizer.recognize_azure(
            audio, key=azKey, language=lang)
    except sr.RequestError:
        # API was unreachable or unresponsive
        response["success"] = False
        response["error"] = "API unavailable"
    except sr.UnknownValueError:
        # speech was unintelligible
        response["error"] = "Unable to recognize speech"

    return response


def listen_and_interpret(len, lang="de-DE"):
    # Record audio for a given time
    wav_name = record_wav(
        len, "interpret" + datetime.datetime.now().strftime('%Y-%m-%d_%H.%M.%S'))
    r = sr.Recognizer()
    # Analyze recorder audio with google
    return interpret_wav(wav_name, r, lang)


def listen_and_playback(len, pitcher, interpret=False, lang="de-DE"):
    # Record audio for a given time
    wav_name = record_wav(
        len, "playback" + datetime.datetime.now().strftime('%Y-%m-%d_%H.%M.%S'))
    # Interpet and play back if wanted
    if interpret:
        r = sr.Recognizer()
        talked = interpret_wav(wav_name, r, lang)
        play_audio(make_speech(talked["transcription"],
                               "de"), settings["laut"], settings["schnell"])
    else:
        play_audio(wav_name, pitcher)


def speak(speech, pitch=0, language="de"):
    play_audio(make_speech(speech, language), pitch)


def make_speech(speech, language="de"):
    filename = 'speak.wav'
    tts = gTTS(text=speech, lang=language).save(filename)
    return filename


def transform_wav(wavname, steps=4, rate=11000):
    y, sr = librosa.load(wavname, sr=rate)
    y_shifted = librosa.effects.pitch_shift(y, sr, n_steps=steps)
    librosa.output.write_wav(wavname, y_shifted, sr)
    # return re.sub(".wav", "_trans.wav", wavname)
    return wavname


def play_audio(filename, modulate, wait=True):
    """ Helper function to play audio files in Linux """
    if modulate != 0:
        filename = transform_wav(filename, modulate)
    play_cmd = "mplayer -volume 95 ./{}".format(filename)
    syscmd(play_cmd, wait)


def is_time_between(begin_time, end_time, check_time=None):
    # If check time is not given, default to current UTC time
    check_time = check_time or datetime.datetime.utcnow().time()
    if begin_time < end_time:
        return check_time >= begin_time and check_time <= end_time
    else:  # crosses midnight
        return check_time >= begin_time or check_time <= end_time
