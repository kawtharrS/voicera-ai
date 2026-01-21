import 'package:flutter/material.dart';
import 'package:mobile/screens/chat/voice_controller.dart';

class VoiceStatus extends StatelessWidget {
  final VoiceState state;
  final String voice;

  const VoiceStatus({required this.state, required this.voice});

  @override
  Widget build(BuildContext context) {
    if (state == VoiceState.speaking) {
      return Text('Speaking with $voice');
    }
    return Text(state.name);
  }
}
