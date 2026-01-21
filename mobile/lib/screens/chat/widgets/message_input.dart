import 'package:flutter/material.dart';

class MessageInput extends StatelessWidget {
  final String text;
  final ValueChanged<String> onChanged;
  final VoidCallback onSend;

  const MessageInput({
    required this.text,
    required this.onChanged,
    required this.onSend,
  });

  @override
  Widget build(BuildContext context) {
    return TextField(
      textAlign: TextAlign.center,
      onChanged: onChanged,
      decoration: InputDecoration(
        hintText: 'Type your message...',
        suffixIcon: IconButton(
          icon: const Icon(Icons.send),
          onPressed: onSend,
        ),
      ),
    );
  }
}
