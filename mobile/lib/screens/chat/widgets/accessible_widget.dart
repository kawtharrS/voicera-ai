import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../voice_controller.dart';
import 'package:mobile/constants/colors.dart';

class AccessibleWidget extends StatefulWidget {
  final Widget child;
  final String label;
  final VoidCallback onTap;
  final VoidCallback? onLongPress;
  final VoidCallback? onSwipeUp;
  final double borderRadius;

  const AccessibleWidget({
    super.key,
    required this.child,
    required this.label,
    required this.onTap,
    this.onLongPress,
    this.onSwipeUp,
    this.borderRadius = 8,
  });

  @override
  State<AccessibleWidget> createState() => AccessibleWidgetState();
}

class AccessibleWidgetState extends State<AccessibleWidget> {
  bool isHovering = false;

  @override
  Widget build(BuildContext context) {
    final focusedLabel = context.select<VoiceChatController, String?>(
      (c) => c.focusedElementLabel,
    );
    final bool isHighlighted = focusedLabel == widget.label;

    return MouseRegion(
      onEnter: (_) => handleEnter(),
      onExit: (_) => handleExit(),
      child: GestureDetector(
        behavior: HitTestBehavior.opaque,

        onPanUpdate: (details) {
          final RenderBox? box = context.findRenderObject() as RenderBox?;
          if (box != null) {
            final local = box.globalToLocal(details.globalPosition);
            if (box.paintBounds.contains(local)) {
              handleEnter();
            } else {
              handleExit();
            }
          }
        },
        
        onPanEnd: (details) {
          handleExit();
          // Use dy velocity from pixelsPerSecond for more reliable swipe detection in a Pan gesture.
          // Negative dy means upward movement.
          if (isHighlighted && details.velocity.pixelsPerSecond.dy < -300) {
            widget.onSwipeUp?.call();
          }
        },
        onPanCancel: () => handleExit(),

        onTap: () {
          if (isHighlighted) {
            final controller = context.read<VoiceChatController>();
            widget.onTap();
            controller.setFocus(null);
          }
        },
        
        onLongPress: widget.onLongPress,

        child: AnimatedContainer(
          duration: const Duration(milliseconds: 20),
          decoration: BoxDecoration(
            border: Border.all(
              color: isHighlighted ? AppColors.orange : Colors.transparent,
              width: 3,
            ),
            borderRadius: BorderRadius.circular(widget.borderRadius),
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
            child: widget.child,
          ),
        ),
      ),
    );
  }

  void handleEnter() {
    if (!isHovering) {
      isHovering = true;
      final controller = context.read<VoiceChatController>();
      controller.setFocus(widget.label);
      controller.speak(widget.label);
    }
  }

  void handleExit() {
    if (isHovering) {
      isHovering = false;
    }
  }
}
