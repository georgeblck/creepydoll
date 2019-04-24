import random
import time
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


from os.path import basename
import speech_recognition as sr


def speak(speech, language="en"):
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


def recognize_speech_from_mic(recognizer, microphone, lang, listenlength=10., phraselength=5.):
    """Transcribe speech from recorded from `microphone`.

    Returns a dictionary with three keys:
    "success": a boolean indicating whether or not the API request was
               successful
    "error":   `None` if no error occured, otherwise a string containing
               an error message if the API could not be reached or
               speech was unrecognizable
    "transcription": `None` if speech could not be transcribed,
               otherwise a string containing the transcribed text
    """
    # check that recognizer and microphone arguments are appropriate type
    if not isinstance(recognizer, sr.Recognizer):
        raise TypeError("`recognizer` must be `Recognizer` instance")

    if not isinstance(microphone, sr.Microphone):
        raise TypeError("`microphone` must be `Microphone` instance")

    # adjust the recognizer sensitivity to ambient noise and record audio
    # from the microphone
    with microphone as source:
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source, timeout=listenlength, phrase_time_limit=phraselength)

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
    except sr.WaitTimeoutError:
        response["error"] = "Too long. Didn't wait"

    return response


if __name__ == "__main__":

    # create recognizer and mic instances
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()
    NUM_GUESSES = 5
    PROMPT_LIMIT = 5
    for i in range(NUM_GUESSES):
        # get the guess from the user
        # if a transcription is returned, break out of the loop and
        #     continue
        # if no transcription returned and API request failed, break
        #     loop and continue
        # if API request succeeded but no transcription was returned,
        #     re-prompt the user to say their guess again. Do this up
        #     to PROMPT_LIMIT times
        for j in range(PROMPT_LIMIT):
            print('Guess {}. Speak!'.format(i + 1))
            guess = recognize_speech_from_mic(recognizer, microphone, "de-DE")
            print(guess["transcription"])
            print(guess["error"])
            if guess["transcription"]:
                break
            if not guess["success"]:
                break
            print("I didn't catch that. What did you say?\n")

        # if there was an error, stop the game
        if guess["error"]:
            print("ERROR: {}".format(guess["error"]))
            break

        # show the user the transcription
        print("You said: {}".format(guess["transcription"]))
        speak(guess["transcription"])
        # determine if guess is correct and if any attempts remain
        guess_is_correct = False
        user_has_more_attempts = True
        # determine if the user has won the game
        # if not, repeat the loop if user has more attempts
        # if no attempts left, the user loses the game
        if guess_is_correct:
            print("Correct! You win!".format(word))
            break
        elif user_has_more_attempts:
            print("Incorrect. Try again.\n")
        else:
            print("Sorry, you lose!\nI was thinking of '{}'.".format(word))
            break
