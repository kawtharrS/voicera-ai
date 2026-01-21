import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'voice_controller.dart';
import 'widgets/voice_orb.dart';
import 'widgets/message_input.dart';
import 'widgets/voice_status.dart';
import 'widgets/voice_selector.dart';

class VoiceChatPage extends StatelessWidget {
  const VoiceChatPage({super.key});

  @override
  Widget build(BuildContext context) {
    final controller = context.watch<VoiceChatController>();

    return Scaffold(
      backgroundColor: Colors.white,
      body: SafeArea(
        child: Column(
          children: [
            VoiceSelector(
              selectedVoice: controller.selectedVoice,
              onVoiceSelected: controller.setVoice,
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
                  MessageInput(
                    text: controller.transcription,
                    onChanged: controller.updateText,
                    onSend: controller.sendText,
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
