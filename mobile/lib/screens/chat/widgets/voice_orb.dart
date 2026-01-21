import 'package:flutter/material.dart';
import 'package:mobile/screens/chat/voice_controller.dart';

class VoiceOrb extends StatelessWidget {
  final VoiceState state;
  final VoidCallback onTap;
  final VoidCallback onLongPress;

  const VoiceOrb({
    required this.state,
    required this.onTap,
    required this.onLongPress,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      onLongPress: onLongPress,
      child: CircleAvatar(
        radius: 90,
        backgroundColor: Colors.teal,
        child: Text(
          state.name.toUpperCase(),
          style: const TextStyle(color: Colors.white),
        ),
      ),
    );
  }
}
