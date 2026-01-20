import 'package:flutter/material.dart';
import 'package:flutter/semantics.dart';
import 'package:flutter/services.dart';
import 'package:mobile/constants/colors.dart';
import 'package:mobile/constants/paddings.dart';

class VoiceChatPage extends StatefulWidget{
    const voiceChatPage({Key? key}) : super(key:key);

    @override
    State<VoiceChatPage> createState() => VoiceChatState();
}
class VoiceChatState extends State<VoiceChatPage> 
    with TickerProviderStateMixin {
        late AnimationController pulseController;
        late AnimationController waveController;
        bool isRecording = false;

        @override
        void initState(){
            super.initState();

            pulseController = AnimationController(
                duration: const Duration(milliseconds:2000),
                vsync: this,
            )..repeat();

            waveController = AnimationController(
                duration:const Duration(milliseconds: 1500),
                vsync:this,
            )..repeat();
        }

        @override
        void dispose(){
            pulseController.dispose();
            waveController.dispose();
            super.dispose();
        }

        Future<void> toggleRecording() async {
            setState((){
                isRecording = !isRecording;
            });
            String announcement = isRecording ? 'Listening Started' : 'Recording Stopped';
            await SemanticsService.announce(
                announcement,
                TextDirection.ltr,
            );
        }

        
    }