import pyttsx3
import settings

class TTSManager:
    def __init__(self):
        self.enabled = getattr(settings, 'TTS_ENABLED', True)
        self.rate = getattr(settings, 'TTS_RATE', 150)
        
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', self.rate)
            self.engine.setProperty('volume', 1.0)
            
            # Identify voices
            self.voices = self.engine.getProperty('voices')
            self.pt_voice = None
            self.en_voice = None
            for voice in self.voices:
                if 'PT-BR' in voice.id.upper() or 'PORTUGUESE' in voice.name.upper():
                    self.pt_voice = voice.id
                if 'EN-US' in voice.id.upper() or 'ZIRA' in voice.name.upper():
                    self.en_voice = voice.id
            
            # Start loop in non-blocking mode
            self.engine.startLoop(False)
            print("TTS Engine initialized with startLoop(False)")
        except Exception as e:
            print(f"Failed to initialize pyttsx3: {e}")
            self.engine = None

    def update(self):
        if self.enabled and self.engine:
            try:
                self.engine.iterate()
            except Exception:
                pass

    def speak(self, text, lang='en', interrupt=True):
        if not self.enabled or not self.engine:
            return
        
        print(f"TTS Speak: {text}")
        if interrupt:
            try:
                self.engine.stop()
            except:
                pass

        # Set voice
        voice_id = self.en_voice if lang == 'en' else self.pt_voice
        if voice_id:
            self.engine.setProperty('voice', voice_id)
        
        self.engine.say(text)

    def stop(self):
        if self.engine:
            try:
                self.engine.endLoop()
            except:
                pass
