import speech_recognition as sr

def listen(timeout=5, phrase_time_limit=15):
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
    return recognizer.recognize_google(audio)
