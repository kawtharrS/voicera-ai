import 'package:speech_to_text/speech_to_text.dart' as stt;
import 'package:permission_handler/permission_handler.dart';

class SpeechService {
  final stt.SpeechToText _speech = stt.SpeechToText();
  bool _isInitialized = false;

  Future<bool> init() async {
    try {
      var status = await Permission.microphone.status;
      
      if (status.isDenied) {
        status = await Permission.microphone.request();
      }
      
      if (status.isPermanentlyDenied) {
        return false;
      }
      
      if (!status.isGranted) {
        return false;
      }
      
      _isInitialized = await _speech.initialize(
      );

      return _isInitialized;
    } catch (e) {
      return false;
    }
  }

  void listen(void Function(String text, bool finalResult) onResult) {
    if (!_isInitialized) {
      return;
    }

    if (!_speech.isAvailable) {
      return;
    }

    _speech.listen(
      onResult: (result) {
        onResult(result.recognizedWords, result.finalResult);
      },
      listenOptions: stt.SpeechListenOptions(
        listenMode: stt.ListenMode.confirmation,
        partialResults: true,
      ),
    );
  }

  Future<void> stop() async {
    if (_speech.isListening) {
      await _speech.stop();
    }
  }

  Future<bool> checkAndRequestMicrophonePermission() async {
    var status = await Permission.microphone.status;
    
    if (status.isDenied) {
      status = await Permission.microphone.request();
    }
    
    return status.isGranted;
  }

  Future<String> getPermissionStatus() async {
    final status = await Permission.microphone.status;
    
    if (status.isGranted) return 'granted';
    if (status.isDenied) return 'denied';
    if (status.isPermanentlyDenied) return 'permanentlyDenied';
    if (status.isRestricted) return 'restricted';
    
    return 'unknown';
  }

  bool get isInitialized => _isInitialized;
  bool get isListening => _speech.isListening;
}
