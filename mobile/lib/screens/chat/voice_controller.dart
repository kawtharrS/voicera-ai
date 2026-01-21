import 'package:flutter/foundation.dart';
import 'services/tts_service.dart';
import 'services/agent_service.dart';
import 'services/speech_service.dart';

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

  VoiceChatController({
    required this.tts,
    required this.agent,
    required this.speech,
  });

  void setVoice(String voice) {
    selectedVoice = voice;
    notifyListeners();
  }

  void updateText(String text) {
    transcription = text;
    notifyListeners();
  }

  Future<void> toggleListening() async {
    if (state == VoiceState.listening) {
      await speech.stop();
      state = VoiceState.idle;
    } else {
      await startListening();
    }
    notifyListeners();
  }

  Future<void> startListening() async {
    state = VoiceState.listening;
    notifyListeners();

    speech.listen((text, isFinal) {
      transcription = text;
      notifyListeners();

      if (isFinal) {
        sendText();
      }
    });

    await tts.speak('Listening', selectedVoice);
  }

  Future<void> sendText() async {
    if (transcription.isEmpty) return;

    state = VoiceState.thinking;
    notifyListeners();

    final answer = await agent.ask(transcription);

    transcription = answer;
    state = VoiceState.speaking;
    notifyListeners();

    await tts.speak(answer, selectedVoice);

    state = VoiceState.idle;
    notifyListeners();
  }

  void readCurrentText() {
    if (transcription.isNotEmpty) {
      tts.speak(transcription, selectedVoice);
    }
  }
}
