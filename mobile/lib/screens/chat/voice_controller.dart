import 'package:flutter/material.dart';
import 'package:mobile/apis/auth_service.dart';
import 'package:mobile/services/notification_service.dart';
import 'services/tts_service.dart';
import 'services/agent_service.dart';
import 'services/speech_service.dart';
import 'services/image_service.dart';
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
  final ImageDescribeService imageService;

  VoiceState state = VoiceState.idle;
  String transcription = '';
  String selectedVoice = 'alloy';
  bool isInitialized = false;
  String? focusedElementLabel;

  VoiceChatController({
    required this.tts,
    required this.agent,
    required this.speech,
    required this.imageService,
  }) {
    _init();
  }

  Future<void> _init() async {
    final speechInitialized = await speech.init();
    
    if (!speechInitialized) {
      state = VoiceState.error;
      notifyListeners();
      return;
    }
    
    await testConnection();
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
    if (!isInitialized) {
      tts.speak('Speech recognition is still initializing. Please wait.', selectedVoice);
      return;
    }

    if (!speech.isInitialized) {
      state = VoiceState.error;
      notifyListeners();
      return;
    }

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
      notifyListeners();
      
      await tts.speak('Processing your question', selectedVoice);
    }
  }

  Future<void> sendText([String? text]) async {
    final message = text ?? transcription;
    if (message.isEmpty) {
      await tts.speak('Please say something or type a message', selectedVoice);
      return;
    }

    state = VoiceState.thinking;
    notifyListeners();

    try {
      final result = await agent.ask(message);
      final answer = result.response;
      transcription = answer;
      state = VoiceState.speaking;
      notifyListeners();

      final negativeEmotions = ['sadness', 'anger', 'fear', 'disgust'];      
      if (negativeEmotions.contains(result.emotion.toLowerCase())) {
        debugPrint('Negative emotion detected: ${result.emotion}. Scheduling check-in in 1 minute.');
        await NotificationService().scheduleCheckIn(minutes: 1);
      }
      await tts.speak(answer, selectedVoice);
      state = VoiceState.idle;
    } catch (e) {
      state = VoiceState.error;
      notifyListeners();
      
      await tts.speak('Sorry, I encountered an error. $e', selectedVoice);
      
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

    _speakAsync(textToRead);
  }

  Future<void> _speakAsync(String text) async {
    try {
      await tts.speak(text, selectedVoice);
    } catch (e) {
      debugPrint('Error speaking: $e');
    }
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

  Future<void> describeFromCamera() async {
    try {
      state = VoiceState.thinking;
      notifyListeners();

      await tts.speak('Let me look around and describe what I see.', selectedVoice);

      final description = await imageService.captureAndDescribe();
      
      if (description == null) {
        state = VoiceState.idle;
        notifyListeners();
        return;
      }

      transcription = description;
      state = VoiceState.speaking;
      notifyListeners();

      await tts.speak(description, selectedVoice);
      state = VoiceState.idle;
      notifyListeners();
    } catch (e) {
      state = VoiceState.error;
      notifyListeners();
      
      await tts.speak("Sorry, I couldn't describe that image.", selectedVoice);
      
      state = VoiceState.idle;
      notifyListeners();
    }
  }
}