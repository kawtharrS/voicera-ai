import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../voice_controller.dart';
import 'package:mobile/constants/colors.dart';

class AccessibleWidget extends StatelessWidget {
  final Widget child;
  final String label;
  final VoidCallback onTap;
  final VoidCallback? onLongPress;
  final double borderRadius;

  const AccessibleWidget({
    super.key,
    required this.child,
    required this.label,
    required this.onTap,
    this.onLongPress,
    this.borderRadius = 8,
  });

  @override
  Widget build(BuildContext context) {
    final focusedLabel = context.select<VoiceChatController, String?>(
      (c) => c.focusedElementLabel,
    );
    final bool isHighlighted = focusedLabel == label;

    return GestureDetector(
      behavior: HitTestBehavior.opaque,
      onLongPress: onLongPress,
      onTapDown: (_) {
        final controller = context.read<VoiceChatController>();
        controller.setFocus(label);
        controller.speak(label);
      },
      onTap: () {
        final controller = context.read<VoiceChatController>();
        onTap();
        controller.setFocus(null);
      },
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        decoration: BoxDecoration(
          border: Border.all(
            color: isHighlighted ? AppColors.orange : Colors.transparent,
            width: 3,
          ),
          borderRadius: BorderRadius.circular(borderRadius),
          boxShadow: isHighlighted
              ? [
                  BoxShadow(
                    color: AppColors.orange.withOpacity(0.3),
                    blurRadius: 8,
                    spreadRadius: 2,
                  )
                ]
              : [],
        ),
        child: AbsorbPointer(
          absorbing: true,
          child: child,
        ),
      ),
    );
  }
}
