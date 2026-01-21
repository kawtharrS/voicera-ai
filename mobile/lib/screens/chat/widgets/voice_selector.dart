import 'package:flutter/material.dart';

class VoiceSelector extends StatelessWidget {
  final String selectedVoice;
  final ValueChanged<String> onVoiceSelected;

  const VoiceSelector({
    required this.selectedVoice,
    required this.onVoiceSelected,
  });

  @override
  Widget build(BuildContext context) {
    final voices = ['alloy', 'echo', 'fable', 'onyx'];

    return DropdownButton<String>(
      value: selectedVoice,
      items: voices
          .map((v) => DropdownMenuItem(value: v, child: Text(v)))
          .toList(),
      onChanged: (v) => onVoiceSelected(v!),
    );
  }
}
