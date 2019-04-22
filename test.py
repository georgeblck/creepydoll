import speech_recognition as sr
import pyaudio
import wave
import subprocess
import os
import datetime
import re
from gtts import gTTS
import numpy as np
import random
from num2words import num2words


def syscmd(cmd):
    DEVNULL = open(os.devnull, 'wb')
    p = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE,
                         stdout=DEVNULL, stderr=subprocess.STDOUT)
    p.wait()


def record_wav(length, filename):
    FORMAT = pyaudio.paInt16
    CHANNELS = 2
    RATE = 44100
    CHUNK = 1024
    RECORD_SECONDS = length
    WAVE_OUTPUT_FILENAME = "recordings/" + filename + ".wav"
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
    return WAVE_OUTPUT_FILENAME


def interpret_wav(wavname, recognizer, lang):
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
        response["transcription"] = recognizer.recognize_google(
            audio, language=lang)
    except sr.RequestError:
        # API was unreachable or unresponsive
        response["success"] = False
        response["error"] = "API unavailable"
    except sr.UnknownValueError:
        # speech was unintelligible
        response["error"] = "Unable to recognize speech"

    return response


def listen_and_interpret(len=10, lang="en-US"):
    wav_name = record_wav(
        len, "sleep" + datetime.datetime.now().strftime('%Y-%m-%d_%H.%M.%S'))
    r = sr.Recognizer()
    return interpret_wav(wav_name, r, lang)


def listen_and_playback(len, settings, interpret = False):
    wav_name = record_wav(
        len, "playback" + datetime.datetime.now().strftime('%Y-%m-%d_%H.%M.%S'))
    play_mp3(wav_name, settings["laut"], settings["schnell"])


def make_speech(speech, language="de"):
    filename = 'speak.mp3'
    tts = gTTS(text=speech, lang=language).save(filename)
    return filename


def play_mp3(filename, loudness=100, speed=1):
    """ Helper function to play audio files in Linux """
    play_cmd = "mplayer -volume {} -speed {} ./{}".format(
        loudness, speed, filename)
    syscmd(play_cmd)


def button_talk(settings, counter):
    play_mp3(make_speech(num2words(counter, lang=settings["lang"]) + " people have pushed my button. Please push the button. I want you to push my button.",
                         settings["lang"]), settings["laut"], settings["schnell"])

#yas = listen_and_interpret()
#x = re.search("Stop", yas["transcription"])
# print(x)


settings = {
    "path": random.choice(
        ["button", "parrot_raw", "parrot_recog", "talk_back", "play_sounds"]),
    "laut": random.randint(70, 100),
    "schnell": round(np.random.uniform(0.3, 1.8), 3),
    "lang": random.choice(["de", "en"])
}
buttonCounter = 0
print(settings)
listen_and_playback(10, settings)
#button_talk(settings, buttonCounter)
#play_mp3("creepy_laugh.mp3", 100, 1.7)
#schnell = round(np.random.uniform(0.2,2),3)
# print(schnell)
#laut = random.randint(70,100)
#play_mp3(make_speech(num2words(2)+" Koener habe ich"), laut, schnell)
