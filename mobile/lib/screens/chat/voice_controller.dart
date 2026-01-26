import 'package:flutter/material.dart';
import 'package:mobile/apis/auth_service.dart';
import 'services/tts_service.dart';
import 'services/agent_service.dart';
import 'services/speech_service.dart';
import 'package:http/http.dart' as http;

enum VoiceState {
  idle,
  listening,
  thinking,
  speaking,
  error,
}

class VoiceChatController extends ChangeNotifier {
  final TtsService tts;
  final AgentService agent;
  final SpeechService speech;

  VoiceState state = VoiceState.idle;
  String transcription = '';
  String selectedVoice = 'alloy';
  bool isInitialized = false;
  String? focusedElementLabel;

  VoiceChatController({
    required this.tts,
    required this.agent,
    required this.speech,
  }) {
    _init();
  }

  Future<void> _init() async {
    await speech.init();
    await testConnection();

    debugPrint('Pre-generating common TTS phrases...');
    await tts.preGenerateCommonPhrases(voice: selectedVoice);

    isInitialized = true;
    notifyListeners();
  }

  Future<void> testConnection() async {
    try {
      final ttsBaseUrl = AuthService.baseUrl;
      final goBaseUrl = AuthService.goBaseUrl;

      if (ttsBaseUrl != null) {
        await http.get(
          Uri.parse('$ttsBaseUrl/api/tts?text=test'),
          headers: AuthService.headers,
        ).timeout(const Duration(seconds: 3));
      }

      if (goBaseUrl != null) {
        await http.get(
          Uri.parse('$goBaseUrl/health'),
          headers: AuthService.headers,
        ).timeout(const Duration(seconds: 3));
      }
    } catch (e) {
      debugPrint('Connection Failed: $e');
      state = VoiceState.error;
      notifyListeners();
    }
  }

  void setVoice(String voice) {
    selectedVoice = voice;
    tts.speak('Selected $voice voice', selectedVoice);
    notifyListeners();
  }

  void updateText(String text) {
    transcription = text;
    notifyListeners();
  }

  Future<void> toggleListening() async {
    if (state == VoiceState.listening) {
      await stopListening();
    } else {
      await startListening();
    }
  }

  Future<void> startListening() async {
    state = VoiceState.listening;
    notifyListeners();

    tts.speak('Listening', selectedVoice);

    speech.listen((text, isFinal) {
      transcription = text;
      notifyListeners();

      if (isFinal) {
        stopListening();
        sendText(text);
      }
    });
  }

  Future<void> stopListening() async {
    await speech.stop();
    if (state == VoiceState.listening) {
      state = VoiceState.idle;
      tts.speak('Processing your question', selectedVoice);
      notifyListeners();
    }
  }

  /// Sends [text] (or the current transcription) to the agent.
  Future<void> sendText([String? text]) async {
    final message = text ?? transcription;
    if (message.isEmpty) {
      tts.speak('Please say something or type a message', selectedVoice);
      return;
    }

    state = VoiceState.thinking;
    notifyListeners();

    try {
      final answer = await agent.ask(message);
      transcription = answer;
      state = VoiceState.speaking;
      notifyListeners();

      await tts.speak(answer, selectedVoice);
      state = VoiceState.idle;
    } catch (e) {
      state = VoiceState.error;
      tts.speak('Sorry, I encountered an error. $e', selectedVoice);
    } finally {
      notifyListeners();
    }
  }

  void readCurrentText() {
    String textToRead;

    if (transcription.isNotEmpty) {
      textToRead = transcription;
    } else if (state == VoiceState.listening) {
      textToRead = 'Currently listening, please speak';
    } else {
      textToRead = 'Press the circle to speak or type a message';
    }

    tts.speak(textToRead, selectedVoice);
  }

  void setFocus(String? label) {
    focusedElementLabel = label;
    notifyListeners();
  }

  Future<void> speak(String text) async {
    try {
      await tts.speak(text, selectedVoice);
    } catch (e) {
      debugPrint('Error speaking: $e');
    }
}
}
