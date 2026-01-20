import 'package:flutter/material.dart';
import 'package:flutter/semantics.dart';
import 'package:flutter/services.dart';
import 'package:mobile/constants/colors.dart';

class VoiceChatPage extends StatefulWidget {
  const VoiceChatPage({Key? key}) : super(key: key);

  @override
  State<VoiceChatPage> createState() => VoiceChatState();
}

class VoiceChatState extends State<VoiceChatPage>
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

  Future<void> _toggleRecording() async {
    setState(() {
      isRecording = !isRecording;
    });

    String announcement = isRecording ? 'Listening started' : 'Recording stopped';
    await SemanticsService.announce(
        announcement,
        TextDirection.ltr,
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      body: SafeArea(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [

            Padding(
              padding: const EdgeInsets.all(16),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Semantics(
                    button: true,
                    enabled: true,
                    label: 'Go back',
                    child: IconButton(
                      icon: const Icon(Icons.arrow_back),
                      onPressed: () => Navigator.pop(context),
                      tooltip: 'Go back to previous screen',
                    ),
                  ),
                  const Text(
                    'Voicera Voice Chat',
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  Semantics(
                    button: true,
                    enabled: true,
                    label: 'More options',
                    child: IconButton(
                      icon: const Icon(Icons.more_vert),
                      onPressed: () {},
                      tooltip: 'More options menu',
                    ),
                  ),
                ],
              ),
            ),

            Expanded(
              child: Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [

                    Stack(
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
                          onTap: _toggleRecording,
                          child: Semantics(
                            button: true,
                            enabled: true,
                            label: isRecording
                                ? 'Stop recording'
                                : 'Tap to speak',
                            child: Tooltip(
                              message: isRecording
                                  ? 'Tap to stop recording'
                                  : 'Tap to start recording',
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
                                      AppColors.teal.withOpacity(0.7),
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
                                      Text(
                                        isRecording
                                            ? 'Listening...'
                                            : 'Tap to speak',
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
                        ),
                      ],
                    ),
                    const SizedBox(height: 40),
                    Semantics(
                      label: isRecording
                          ? 'Currently listening, speak clearly into the microphone'
                          : 'Press the circle button and speak clearly',
                      child: Text(
                        isRecording
                            ? 'Speak clearly into the microphone'
                            : 'Press the circle and speak',
                        style: const TextStyle(
                          color: Colors.black54,
                          fontSize: 14,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}