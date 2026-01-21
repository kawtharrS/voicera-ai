import 'package:speech_to_text/speech_to_text.dart' as stt;

class SpeechService {
  final stt.SpeechToText _speech = stt.SpeechToText();

  Future<bool> init() => _speech.initialize();

  void listen(void Function(String text, bool finalResult) onResult) {
    _speech.listen(
      onResult: (result) {
        onResult(result.recognizedWords, result.finalResult);
      },
    );
  }

  Future<void> stop() => _speech.stop();
}
