import 'package:flutter/material.dart';
import 'package:mobile/screens/chat/voice_controller.dart';
import 'package:mobile/constants/colors.dart';

class VoiceStatus extends StatelessWidget {
  final VoiceState state;
  final String voice;

  const VoiceStatus({super.key, required this.state, required this.voice});

  @override
  Widget build(BuildContext context) {
    bool isRecording = state == VoiceState.listening;
    bool isSpeaking = state == VoiceState.speaking;

    return Column(
      children: [
        const SizedBox(height: 10),
        Text(
          isRecording
              ? 'Listening to you...'
              : (state != VoiceState.error ? 'Tap to speak or type a message.' : 'Microphone not available. Check permissions in settings.'),
          style: const TextStyle(
            color: Colors.black54,
            fontSize: 13,
          ),
        ),
        const SizedBox(height: 20),
        if (isSpeaking)
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            decoration: BoxDecoration(
              color: AppColors.orange.withOpacity(0.1),
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: AppColors.orange),
            ),
            child: Text(
              'Speaking with $voice voice...',
              style: const TextStyle(
                color: Colors.black87,
                fontSize: 12,
              ),
            ),
          ),
        if (!isSpeaking && voice != 'alloy')
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            decoration: BoxDecoration(
              color: AppColors.teal.withOpacity(0.1),
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: AppColors.teal),
            ),
            child: Text(
              'Current voice: $voice',
              style: const TextStyle(
                color: Colors.black87,
                fontSize: 12,
              ),
            ),
          ),
      ],
    );
  }
}
