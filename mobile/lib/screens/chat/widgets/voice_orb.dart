import 'package:flutter/material.dart';
import 'package:mobile/screens/chat/voice_controller.dart';
import 'package:mobile/theme/theme.dart';

class VoiceOrb extends StatefulWidget {
  final VoiceState state;
  final VoidCallback onTap;
  final VoidCallback onLongPress;
  final VoidCallback? onSwipeUp;

  const VoiceOrb({
    super.key,
    required this.state,
    required this.onTap,
    required this.onLongPress,
    this.onSwipeUp,
  });

  @override
  State<VoiceOrb> createState() => _VoiceOrbState();
}

class _VoiceOrbState extends State<VoiceOrb> with TickerProviderStateMixin {
  late AnimationController waveController;

  @override
  void initState() {
    super.initState();
    waveController = AnimationController(
      duration: const Duration(milliseconds: 1500),
      vsync: this,
    )..repeat();
  }

  @override
  void dispose() {
    waveController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final bool isRecording = widget.state == VoiceState.listening;
    final bool isThinking = widget.state == VoiceState.thinking;
    final bool isSpeaking = widget.state == VoiceState.speaking;

    return Stack(
      alignment: Alignment.center,
      children: [
        AnimatedBuilder(
          animation: waveController,
          builder: (context, child) {
            return Container(
              width: 220,
              height: 220,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                border: Border.all(
                  color: AppColors.teal.withOpacity(
                    isRecording
                        ? 0.2 * (1 - waveController.value)
                        : 0.05,
                  ),
                  width: 18,
                ),
              ),
            );
          },
        ),
        GestureDetector(
          onTap: widget.onTap,
          onLongPress: widget.onLongPress,
          onVerticalDragEnd: (details) {
            // Negative velocity = swipe up.
            if (details.primaryVelocity != null && details.primaryVelocity! < -300) {
              widget.onSwipeUp?.call();
            }
          },
          child: Semantics(
            button: true,
            enabled: true,
            label: isRecording
                ? 'Stop recording button'
                : 'Voice orb. Tap to speak. Long press to read your message aloud.',
            child: Container(
              width: 180,
              height: 180,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                gradient: LinearGradient(
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                  colors: [
                    AppColors.teal,
                    isSpeaking ? Colors.teal : AppColors.teal.withOpacity(0.7),
                  ],
                ),
                boxShadow: [
                  BoxShadow(
                    color: AppColors.teal.withOpacity(0.3),
                    blurRadius: 20,
                    spreadRadius: 5,
                  ),
                ],
              ),
              child: Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    if (isThinking || isSpeaking)
                      const CircularProgressIndicator(
                          color: Colors.white, strokeWidth: 2),
                    if (!isThinking && !isSpeaking)
                      Text(
                        isRecording ? 'Listening...' : 'Tap to speak',
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 14,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ],
    );
  }
}
