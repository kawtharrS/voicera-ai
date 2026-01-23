import 'package:speech_to_text/speech_to_text.dart' as stt;

/// Small wrapper around the speech_to_text plugin.
class SpeechService {
  final stt.SpeechToText _speech = stt.SpeechToText();

  /// Initializes the microphone / speech engine.
  Future<bool> init() => _speech.initialize();

  /// Starts listening and calls [onResult] every time speech is recognized.
  void listen(void Function(String text, bool finalResult) onResult) {
    _speech.listen(
      onResult: (result) {
        onResult(result.recognizedWords, result.finalResult);
      },
      listenMode: stt.ListenMode.confirmation,
    );
  }

  /// Stops listening for speech.
  Future<void> stop() => _speech.stop();
}
