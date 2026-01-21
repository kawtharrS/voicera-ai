import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:just_audio/just_audio.dart';
import 'package:mobile/apis/auth_service.dart';

import 'voice_controller.dart';
import 'widgets/voice_orb.dart';
import 'widgets/message_input.dart';
import 'widgets/voice_status.dart';
import 'widgets/voice_selector.dart';
import 'services/tts_service.dart';
import 'services/agent_service.dart';
import 'services/speech_service.dart';

class VoiceChatPage extends StatelessWidget {
  const VoiceChatPage({super.key});

  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider(
      create: (context) => VoiceChatController(
        tts: TtsService(AudioPlayer(), AuthService.baseUrl ?? ''),
        agent: AgentService(AuthService.goBaseUrl ?? ''),
        speech: SpeechService(),
      ),
      child: const _VoiceChatView(),
    );
  }
}

class _VoiceChatView extends StatelessWidget {
  const _VoiceChatView();

  @override
  Widget build(BuildContext context) {
    final controller = context.watch<VoiceChatController>();

    return Scaffold(
      backgroundColor: Colors.white,
      body: SafeArea(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Padding(
              padding: const EdgeInsets.all(16),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  IconButton(
                    icon: const Icon(Icons.arrow_back),
                    onPressed: () => Navigator.pop(context),
                    tooltip: 'Go back',
                  ),
                  const Text(
                    'Voicera Voice Chat',
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  VoiceSelector(
                    selectedVoice: controller.selectedVoice,
                    onVoiceSelected: controller.setVoice,
                  ),
                ],
              ),
            ),
            Expanded(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  VoiceOrb(
                    state: controller.state,
                    onTap: controller.toggleListening,
                    onLongPress: controller.readCurrentText,
                  ),
                  const SizedBox(height: 20),
                  MessageInput(
                    text: controller.transcription,
                    onChanged: controller.updateText,
                    onSend: controller.sendText,
                    onLongPress: controller.readCurrentText,
                  ),
                  VoiceStatus(
                    state: controller.state,
                    voice: controller.selectedVoice,
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
