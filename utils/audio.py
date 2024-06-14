import azure.cognitiveservices.speech as speechsdk
from utils.config import agent_config

class Azure_audio:
    """
    access the ASR and TTS service
    """
    ssml_string = """
                <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="https://www.w3.org/2001/mstts" xml:lang="en-US">
                    <voice name="en-US-JennyNeural">
                        <mstts:express-as style="assistant" styledegree="1.4">
                            {text}
                        </mstts:express-as>
                    </voice>
                </speak>
                """

    def __init__(self) -> None:
        self.speech_config = speechsdk.SpeechConfig(agent_config.get("Azure_SDK.key"), agent_config.get("Azure_SDK.region"))
        self.speech_config.speech_synthesis_language = agent_config.get("Azure_SDK.speech_synthesis_language")
        self.speech_config.speech_synthesis_voice_name= agent_config.get("Azure_SDK.speech_synthesis_voice_name")

        self.audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)
        self.speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=self.speech_config, audio_config=self.audio_config)
        self.connection = speechsdk.Connection.from_speech_synthesizer(self.speech_synthesizer)
        self.connection.open(True)

        self.speech_recognizer = speechsdk.SpeechRecognizer(speech_config=self.speech_config)


    def asr_(self):
        """
        audio to text through sdk
        """
        result = self.speech_recognizer.recognize_once_async().get()
        return result.text


    def tts_(self, text):
        """
        text to audio through sdk
        """
        # synthesize to the default speaker.
        speech_synthesis_result = self.speech_synthesizer.start_speaking_text_async(text).get()
        audio_data_stream = speechsdk.AudioDataStream(speech_synthesis_result)
        audio_buffer = bytes(16000)
        filled_size = audio_data_stream.read_data(audio_buffer)
        while filled_size > 0:
            filled_size = audio_data_stream.read_data(audio_buffer)


    def tts_ssml(self, text):
        """
        text to audio ssml through sdk
        """
        text = self.ssml_string.replace('{text}', text)
        speech_synthesis_result = self.speech_synthesizer.speak_ssml_async(text).get()

        # 检查合成结果
        if speech_synthesis_result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            audio_data_stream = speechsdk.AudioDataStream(speech_synthesis_result)
            audio_buffer = bytes(16000)
            filled_size = audio_data_stream.read_data(audio_buffer)
            while filled_size > 0:
                filled_size = audio_data_stream.read_data(audio_buffer)

        elif speech_synthesis_result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = speech_synthesis_result.cancellation_details
            print("Speech synthesis canceled: {}".format(cancellation_details.reason))
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                if cancellation_details.error_details:
                    print("Error details: {}".format(cancellation_details.error_details))
        else:
            print("Unexpected synthesis result reason: {}".format(speech_synthesis_result.reason))


audio = Azure_audio()