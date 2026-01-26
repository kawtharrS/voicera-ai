import 'package:speech_to_text/speech_to_text.dart' as stt;
import 'package:permission_handler/permission_handler.dart';
import 'package:flutter/material.dart';

class SpeechService {
  final stt.SpeechToText _speech = stt.SpeechToText();
  bool _isInitialized = false;

  Future<bool> init() async {
    try {
      // Check current permission status
      var status = await Permission.microphone.status;
      debugPrint('Current microphone permission status: $status');
      
      if (status.isDenied) {
        // Request microphone permission
        debugPrint('Requesting microphone permission...');
        status = await Permission.microphone.request();
      }
      
      if (status.isPermanentlyDenied) {
        debugPrint('Microphone permission permanently denied. Please enable in device settings.');
        return false;
      }
      
      if (!status.isGranted) {
        debugPrint('Microphone permission denied by user');
        return false;
      }

      debugPrint('Microphone permission granted. Initializing speech recognition...');
      
      // Initialize speech recognition
      _isInitialized = await _speech.initialize(
        onError: (error) {
          debugPrint('Speech recognition error: ${error.errorMsg}');
        },
        onStatus: (status) {
          debugPrint('Speech recognition status: $status');
        },
      );

      if (_isInitialized) {
        debugPrint('Speech recognition initialized successfully');
      } else {
        debugPrint('Speech recognition failed to initialize. Microphone may not be available.');
      }

      return _isInitialized;
    } catch (e) {
      debugPrint('Error initializing speech service: $e');
      return false;
    }
  }

  void listen(void Function(String text, bool finalResult) onResult) {
    if (!_isInitialized) {
      debugPrint('Speech service not initialized. Cannot listen.');
      return;
    }

    if (!_speech.isAvailable) {
      debugPrint('Speech recognition not available');
      return;
    }

    _speech.listen(
      onResult: (result) {
        debugPrint('Speech result: ${result.recognizedWords} (final: ${result.finalResult})');
        onResult(result.recognizedWords, result.finalResult);
      },
      listenMode: stt.ListenMode.confirmation,
      partialResults: true,
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
