from utils import *
import librosa

def transform_wav(wavname, steps = 4, rate = 44100):
    y, sr = librosa.load(wavname, sr=rate)
    y_shifted = librosa.effects.pitch_shift(y, sr, n_steps=steps)
    librosa.output.write_wav(wavname, y_shifted, sr)
    return re.sub(".wav", "_trans.wav", wavname)

make_speech("In Harry Potter and the Order of Phoenix, we meet one of Harry Potters most hated character, Dolores Umbridge. Can we imagine ourselves into her point of view", "en")
# y is a numpy array of the wav file, sr = sample rate
y, sr = librosa.load('speak.wav', sr=44100)
y_shifted = librosa.effects.pitch_shift(y, sr, n_steps=8)  # sh
librosa.output.write_wav("watup.wav", y_shifted, sr)
play_mp3("watup.wav")
#button_talk(settings, buttonCounter)
#play_mp3("creepy_laugh.mp3", 100, 1.7)
#schnell = round(np.random.uniform(0.2,2),3)
# print(schnell)
#laut = random.randint(70,100)
#play_mp3(make_speech(num2words(2)+" Koener habe ich"), laut, schnell)
