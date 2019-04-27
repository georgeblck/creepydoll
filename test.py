#from utils import *
#import librosa
import speech_recognition as sr

r = sr.Recognizer()

with sr.AudioFile('testi.wav') as source:
    audio = r.record(source)

print(r.recognize_azure(audio, key = "929ceac53b6144b98bf2bcec94077198", language = "de-DE"))


#make_speech("In Harry Potter and the Order of Phoenix, we meet one of Harry Potters most hated character, Dolores Umbridge. Can we imagine ourselves into her point of view", "en")
# y is a numpy array of the wav file, sr = sample rate
#y, sr = librosa.load('speak.wav', sr=44100)
#y_shifted = librosa.effects.pitch_shift(y, sr, n_steps=8)  # sh
#librosa.output.write_wav("watup.wav", y_shifted, sr)
#play_mp3("watup.wav")
#button_talk(settings, buttonCounter)
#play_mp3("creepy_laugh.mp3", 100, 1.7)
#schnell = round(np.random.uniform(0.2,2),3)
# print(schnell)
#laut = random.randint(70,100)
#play_mp3(make_speech(num2words(2)+" Koener habe ich"), laut, schnell)
