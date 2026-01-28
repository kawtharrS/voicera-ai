import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:just_audio/just_audio.dart';
import 'package:mobile/apis/auth_service.dart';
import 'voice_controller.dart';
import 'widgets/voice_orb.dart';
import 'widgets/message_input.dart';
import 'widgets/voice_status.dart';
import 'widgets/voice_selector.dart';
import 'widgets/accessible_widget.dart';
import 'services/tts_service.dart';
import 'services/agent_service.dart';
import 'services/speech_service.dart';
import 'services/image_service.dart';

class VoiceChatPage extends StatelessWidget {
  const VoiceChatPage({super.key});

  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider(
      create: (context) => VoiceChatController(
        tts: TtsService(AudioPlayer(), AuthService.baseUrl),
        agent: AgentService(AuthService.goBaseUrl),
        speech: SpeechService(),
        imageService: ImageDescribeService(),
      ),
      child: const VoiceChatView(),
    );
  }
}

class VoiceChatView extends StatefulWidget {
  const VoiceChatView();

  @override
  State<VoiceChatView> createState() => VoiceChatViewState();
}

class VoiceChatViewState extends State<VoiceChatView> {
  UserInfo? userInfo;

  @override
  void initState() {
    super.initState();
    loadUserInfo();
  }

  Future<void> loadUserInfo() async {
    final info = await AuthService.fetchCurrentUser();
    if (!mounted) return;
    setState(() {
      userInfo = info;
    });
  }

  @override
  Widget build(BuildContext context) {
    final controller = context.watch<VoiceChatController>();
    final bool canTypeMessage = userInfo?.roleId == 2;

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
                  AccessibleWidget(
                    label: 'Go back',
                    onTap: () => Navigator.pop(context),
                    child: const IconButton(
                      icon: Icon(Icons.arrow_back),
                      onPressed: null, 
                    ),
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
                    onVoiceSelected: (voice) {
                      controller.setVoice(voice);
                    },
                  ),
                ],
              ),
            ),
            Expanded(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  AccessibleWidget(
                    label: controller.state == VoiceState.listening
                        ? 'Stop recording'
                        : 'Tap to start speaking.',
                    borderRadius: 110,
                    onTap: controller.toggleListening,
                    onLongPress: controller.readCurrentText,
                    onSwipeUp: controller.describeFromCamera,
                    child: VoiceOrb(
                      state: controller.state,
                      onTap: () {}, 
                      onLongPress: controller.readCurrentText,
                      onSwipeUp: controller.describeFromCamera,
                    ),
                  ),
                  const SizedBox(height: 20),
                  if (canTypeMessage)
                    AccessibleWidget(
                      label: controller.transcription.isEmpty
                          ? 'Message input field. Empty.'
                          : 'Message input field. Current text: ${controller.transcription}',
                      onTap: controller.sendText,
                      onLongPress: controller.readCurrentText,
                      child: MessageInput(
                        text: controller.transcription,
                        onChanged: controller.updateText,
                        onSend: controller.sendText,
                        onLongPress: controller.readCurrentText,
                      ),
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