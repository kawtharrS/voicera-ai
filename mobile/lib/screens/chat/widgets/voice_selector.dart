import 'package:flutter/material.dart';

class VoiceSelector extends StatelessWidget {
  final String selectedVoice;
  final ValueChanged<String> onVoiceSelected;

  const VoiceSelector({
    super.key,
    required this.selectedVoice,
    required this.onVoiceSelected,
  });

  final List<String> voices = const [
    'alloy',
    'echo',
    'fable',
    'onyx',
    'nova',
    'shimmer'
  ];

  void _showVoiceSelector(BuildContext context) {
    showDialog(
      context: context,
      builder: (BuildContext context) {
        return AlertDialog(
          title: const Text('Select Voice'),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: voices.map((voice) {
                return ListTile(
                  title: Text(voice),
                  leading: Radio<String>(
                    value: voice,
                    groupValue: selectedVoice,
                    onChanged: (String? newValue) {
                      if (newValue != null) {
                        onVoiceSelected(newValue);
                        Navigator.pop(context);
                      }
                    },
                  ),
                  onTap: () {
                    onVoiceSelected(voice);
                    Navigator.pop(context);
                  },
                );
              }).toList(),
            ),
          ),
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return IconButton(
      icon: const Icon(Icons.more_vert),
      onPressed: () => _showVoiceSelector(context),
      tooltip: 'Select voice',
    );
  }
}
