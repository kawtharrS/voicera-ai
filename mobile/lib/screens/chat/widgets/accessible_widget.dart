import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../voice_controller.dart';
import 'package:mobile/constants/colors.dart';

class AccessibleWidget extends StatefulWidget {
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
  State<AccessibleWidget> createState() => _AccessibleWidgetState();
}

class _AccessibleWidgetState extends State<AccessibleWidget> {
  bool _isHovering = false;

  @override
  Widget build(BuildContext context) {
    final focusedLabel = context.select<VoiceChatController, String?>(
      (c) => c.focusedElementLabel,
    );
    final bool isHighlighted = focusedLabel == widget.label;

    return MouseRegion(
      onEnter: (_) => _handleEnter(),
      onExit: (_) => _handleExit(),
      child: GestureDetector(
        behavior: HitTestBehavior.opaque,
                
        onPanUpdate: (details) {
          final RenderBox? box = context.findRenderObject() as RenderBox?;
          if (box != null) {
            final local = box.globalToLocal(details.globalPosition);
            if (box.paintBounds.contains(local)) {
              _handleEnter();
            } else {
              _handleExit();
            }
          }
        },
        
        onPanEnd: (_) => _handleExit(),
        onPanCancel: () => _handleExit(),
        
        onTap: () {
          if (isHighlighted) {
            final controller = context.read<VoiceChatController>();
            widget.onTap();
            controller.setFocus(null);
          }
        },
        
        onLongPress: widget.onLongPress,
        
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 200),
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

  void _handleEnter() {
    if (!_isHovering) {
      _isHovering = true;
      final controller = context.read<VoiceChatController>();
      controller.setFocus(widget.label);
      controller.speak(widget.label);
    }
  }

  void _handleExit() {
    if (_isHovering) {
      _isHovering = false;
    }
  }
}
