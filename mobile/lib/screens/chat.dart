import 'dart:math' as math;
import 'package:flutter/material.dart';

class VoiceChatPage extends StatefulWidget {
  const VoiceChatPage({Key? key}) : super(key: key);

  @override
  State<VoiceChatPage> createState() => _VoiceChatPageState();
}

class _VoiceChatPageState extends State<VoiceChatPage>
    with TickerProviderStateMixin {
  late AnimationController pulseController;
  late AnimationController waveController;
  bool isRecording = false;

  @override
  void initState() {
    super.initState();
    pulseController = AnimationController(
      duration: const Duration(milliseconds: 2000),
      vsync: this,
    )..repeat();

    waveController = AnimationController(
      duration: const Duration(milliseconds: 1500),
      vsync: this,
    )..repeat();
  }

  @override
  void dispose() {
    pulseController.dispose();
    waveController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      body: SafeArea(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            // Header
            Padding(
              padding: const EdgeInsets.all(16),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  IconButton(
                    icon: const Icon(Icons.arrow_back, color: Colors.black87),
                    onPressed: () => Navigator.pop(context),
                  ),
                  const Text(
                    'Voice Chat',
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.w600,
                      color: Colors.black87,
                    ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.more_vert, color: Colors.black87),
                    onPressed: () {},
                  ),
                ],
              ),
            ),
            // Center content with animated circle
            Expanded(
              child: Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Stack(
                      alignment: Alignment.center,
                      children: [
                        // Outer pulse rings
                        AnimatedBuilder(
                          animation: pulseController,
                          builder: (context, child) {
                            return Container(
                              width: 240,
                              height: 240,
                              decoration: BoxDecoration(
                                shape: BoxShape.circle,
                                border: Border.all(
                                  color: const Color(0xFFFF9500).withOpacity(
                                    0.3 * (1 - pulseController.value),
                                  ),
                                  width: 3,
                                ),
                              ),
                            );
                          },
                        ),
                        // Wave animation rings
                        AnimatedBuilder(
                          animation: waveController,
                          builder: (context, child) {
                            return Container(
                              width: 220,
                              height: 220,
                              decoration: BoxDecoration(
                                shape: BoxShape.circle,
                                border: Border.all(
                                  color: const Color(0xFF4DB6AC).withOpacity(
                                    0.4 * (1 - waveController.value),
                                  ),
                                  width: 2,
                                ),
                              ),
                            );
                          },
                        ),
                        // Main gradient circle
                        Container(
                          width: 180,
                          height: 180,
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            gradient: LinearGradient(
                              begin: Alignment.topLeft,
                              end: Alignment.bottomRight,
                              colors: [
                                const Color(0xFF4DB6AC),
                                const Color(0xFF4DB6AC).withOpacity(0.7),
                              ],
                            ),
                            boxShadow: [
                              BoxShadow(
                                color: const Color(0xFF4DB6AC).withOpacity(0.3),
                                blurRadius: 20,
                                spreadRadius: 5,
                              ),
                            ],
                          ),
                          child: Center(
                            child: Column(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                AnimatedBuilder(
                                  animation: pulseController,
                                  builder: (context, child) {
                                    return Icon(
                                      Icons.mic,
                                      size:
                                          60 +
                                          (10 *
                                              math.sin(pulseController.value)),
                                      color: Colors.white,
                                    );
                                  },
                                ),
                                const SizedBox(height: 12),
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
                      ],
                    ),
                    const SizedBox(height: 40),
                    Text(
                      'Press the button and speak',
                      style: TextStyle(
                        color: Colors.black54,
                        fontSize: 14,
                        fontWeight: FontWeight.w400,
                      ),
                    ),
                  ],
                ),
              ),
            ),
            // Bottom controls
            Padding(
              padding: const EdgeInsets.all(24),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                children: [
                  // Stop button
                  GestureDetector(
                    onTap: () {
                      setState(() => isRecording = false);
                    },
                    child: Container(
                      width: 56,
                      height: 56,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: const Color(0xFF9B59B6).withOpacity(0.1),
                        border: Border.all(
                          color: const Color(0xFF9B59B6),
                          width: 2,
                        ),
                      ),
                      child: const Icon(
                        Icons.close,
                        color: Color(0xFF9B59B6),
                        size: 24,
                      ),
                    ),
                  ),
                  // Main record button
                  GestureDetector(
                    onTap: () {
                      setState(() => isRecording = !isRecording);
                    },
                    child: Container(
                      width: 70,
                      height: 70,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        gradient: LinearGradient(
                          begin: Alignment.topLeft,
                          end: Alignment.bottomRight,
                          colors: [
                            const Color(0xFFFF9500),
                            const Color(0xFFFF9500).withOpacity(0.8),
                          ],
                        ),
                        boxShadow: [
                          BoxShadow(
                            color: const Color(0xFFFF9500).withOpacity(0.4),
                            blurRadius: 15,
                            spreadRadius: 2,
                          ),
                        ],
                      ),
                      child: Icon(
                        isRecording ? Icons.stop : Icons.mic,
                        color: Colors.white,
                        size: 32,
                      ),
                    ),
                  ),
                  // Settings button
                  GestureDetector(
                    onTap: () {},
                    child: Container(
                      width: 56,
                      height: 56,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: const Color(0xFF4DB6AC).withOpacity(0.1),
                        border: Border.all(
                          color: const Color(0xFF4DB6AC),
                          width: 2,
                        ),
                      ),
                      child: const Icon(
                        Icons.settings,
                        color: Color(0xFF4DB6AC),
                        size: 24,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}