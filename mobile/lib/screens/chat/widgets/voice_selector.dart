import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../voice_controller.dart';
import 'accessible_widget.dart';

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
    final controller = context.read<VoiceChatController>();
    showDialog(
      context: context,
      builder: (BuildContext context) {
        return ChangeNotifierProvider.value(
          value: controller,
          child: AlertDialog(
          title: const Text('Select Voice'),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: voices.map((voice) {
                return AccessibleWidget(
                  label: 'Voice $voice',
                  onTap: () {
                    onVoiceSelected(voice);
                    Navigator.pop(context);
                  },
                  child: ListTile(
                    title: Text(voice),
                    leading: Radio<String>(
                      value: voice,
                      groupValue: selectedVoice,
                      onChanged: null, 
                    ),
                  ),
                );
              }).toList(),
            ),
          ),
        ));
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return AccessibleWidget(
      label: 'Select voice. Current voice is $selectedVoice',
      onTap: () => _showVoiceSelector(context),
      child: const IconButton(
        icon: Icon(Icons.more_vert),
        onPressed: null, 
      ),
    );
  }
}
