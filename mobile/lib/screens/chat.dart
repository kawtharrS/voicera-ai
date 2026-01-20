import 'dart:math' as math;
import 'package:flutter/material.dart';

class VoiceChatPage extends StatefulWidget{
  const VoiceChatPage({Key? key}) : super(key:key);

  @override
  State<VoiceChatPage> createState() => VoiceChatState();
}

class VoiceChatState extends State<VoiceChatPage> with TickerProviderStateMixin{
  late AnimationController pulseController;
  late AnimationController waveController;
  bool isRecording = false;

  @override
  void initState()
  {
    super.initState();
    pulseController = AnimationController(
      duration: const Duration(milliseconds: 2000),
      vsync:this,
    )..repeat();

    waveController = AnimationController(
      duration: const Duration(milliseconds: 1500),
      vsync:this,
    )..repeat();
  }

  @override
  void dispose() {
    pulseController.dispose();
    waveController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context){
    return Scaffold(
      body: SafeArea(child: Column(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Padding( 
            padding: const EdgeInsets.all(16),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children:[
                IconButton(
                  icon: const Icon(Icons.arrow_back, color: Colors.black87),
                  onPressed: () => Navigator.pop(context),
                ),
                const Text(
                  'Voicera Voice Chat',
                  style: TextStyle(
                    fontSize:18,
                    fontWeight: FontWeight.w600,
                    color: Colors.black87,
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.more_vert, color: Colors.black87),
                  onPressed: () {},
                )
              ],
            )),
            Expanded(
              child: Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                )
              )
            )
        ]
      ),)
    );
  }

  

}