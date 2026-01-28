import 'package:flutter/material.dart';
import 'package:mobile/theme/theme.dart';

class MessageInput extends StatefulWidget {
  final String text;
  final ValueChanged<String> onChanged;
  final VoidCallback onSend;
  final VoidCallback onLongPress;

  const MessageInput({
    super.key,
    required this.text,
    required this.onChanged,
    required this.onSend,
    required this.onLongPress,
  });

  @override
  State<MessageInput> createState() => _MessageInputState();
}

class _MessageInputState extends State<MessageInput> {
  late TextEditingController _controller;

  @override
  void initState() {
    super.initState();
    _controller = TextEditingController(text: widget.text);
  }

  @override
  void didUpdateWidget(MessageInput oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.text != _controller.text) {
      _controller.text = widget.text;
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 40),
      child: GestureDetector(
        behavior: HitTestBehavior.translucent,
        onLongPress: widget.onLongPress,
        child: TextField(
          controller: _controller,
          textAlign: TextAlign.center,
          style: const TextStyle(
            color: Colors.black87,
            fontSize: 16,
            fontWeight: FontWeight.w400,
          ),
          decoration: InputDecoration(
            hintText: 'Type your message...',
            hintStyle: const TextStyle(color: Colors.black26),
            suffixIcon: widget.text.isNotEmpty
                ? IconButton(
                    icon: const Icon(Icons.send, color: AppColors.teal),
                    onPressed: widget.onSend,
                  )
                : null,
            border: UnderlineInputBorder(
              borderSide: BorderSide(color: AppColors.purple.withOpacity(0.3)),
            ),
            enabledBorder: UnderlineInputBorder(
              borderSide: BorderSide(color: AppColors.purple.withOpacity(0.3)),
            ),
            focusedBorder: const UnderlineInputBorder(
              borderSide: BorderSide(color: AppColors.purple),
            ),
          ),
          onChanged: widget.onChanged,
        ),
      ),
    );
  }
}
