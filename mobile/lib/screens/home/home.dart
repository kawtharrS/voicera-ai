import 'package:flutter/material.dart';
import 'accessibility.dart';
import 'services.dart';
import 'package:mobile/constants/colors.dart';
import 'package:mobile/constants/paddings.dart';

class HomePage extends StatelessWidget{
  const HomePage({Key? key}):super(key:key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        actions: [
          TextButton(
            onPressed: () {},
            child: const Text('Features', style: TextStyle(color: Colors.black)),
          ),
          TextButton(
            onPressed: () {},
            child: const Text('Accessibility', style: TextStyle(color: Colors.black)),
          ),
          TextButton(
            onPressed: () {},
            child: const Text("Contact", style:TextStyle(color: Colors.black))
          ),
          const SizedBox(width:8),
          Padding(
            padding: const EdgeInsets.all(8.0),
            child: ElevatedButton(
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.orange,
                shape: RoundedRectangleBorder(borderRadius:BorderRadius.circular(20), ),
              ),
            onPressed: () {
              Navigator.pushNamed(context, '/signin');
            },
            child: const Text('Sign In')
            ),
            ),
            const SizedBox(width: AppPadding.vP),
        ],
      ),
      body: SingleChildScrollView(child: Column(children: [
        Container(
          color: Colors.white,
          padding: const EdgeInsets.symmetric(vertical: 60, horizontal: 24),
          child: Column(
            children: [
              const Text(
                "Voicera: Your AI Voice Assistant",
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 48,
                  fontWeight: FontWeight.bold,
                  height:1.2,
                ),
              ),
              const SizedBox(height: 70),
              ElevatedButton(
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.orange, 
                  padding: const EdgeInsets.symmetric(
                    horizontal:40, 
                    vertical:16,
                  ),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(25)),
                ),
                onPressed: () {},
                child: const Text(
                  'Get Started', 
                  style: TextStyle(fontSize: 16),
                ),
              ),
            ],
          ),
        ),
        Padding(
          padding:const EdgeInsets.symmetric(vertical: 60, horizontal: 24), 
          child: Column(
            children:[
              Column(children: [
                ServiceCard(
                  color: AppColors.teal,
                  title: 'VOICE CONTROL',
                  description: 'Control your device with simple commands. Hands-Free operation for maximum productivity',
                  icon: Icons.mic,
                ),
                const SizedBox(height:20),
                ServiceCard(
                  color: const Color(0xFF9B59B6),
                  title: 'AI GENERATED TEXT',
                  description: 'Get intelligent responses powered by advanced AI. Natural language understanding at its best.',
                  icon: Icons.text_fields,
                ),
                const SizedBox(height:20),
                ServiceCard(
                  color: const Color(0xFFFF9500),
                  title:'TASK AUTOMATION',
                  description:'Automate repetitive tasks with voice commands. Save time and focus on what matters.',
                  icon: Icons.check_circle,
                ),
              ],),
            ],
          )),
          Container(
            color: const Color(0xFFF5F5F5),
            padding: const EdgeInsets.symmetric(vertical:60, horizontal:24),
            child: Column(children: [
              const Text(
                'Designed for Accessibility', 
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 36, 
                  fontWeight: FontWeight.bold
                ),
              ),
              const SizedBox(height: AppPadding.vP),
              const Text(
                'AI that understands everyone, built with WCAG standards. Perfect for all users.',
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 16, 
                  color: Colors.grey,
                ),
              ),
            const SizedBox(height: 40),
            SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  AccessibilityIcon(icon: Icons.visibility, label: 'Vision'),
                  const SizedBox(width: 10),
                  AccessibilityIcon(icon: Icons.pan_tool, label: 'Motor'),
                ],)
            ),
            ],)
          ),
          Container(
            color : const Color(0xFF333333),
            padding: const EdgeInsets.all(24),
            child:Column(
              children: [
                const Text(
                  'Voicera',
                  style: TextStyle(
                    color: Color.fromARGB(255, 255, 255, 255),
                    fontSize: 20, 
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height:AppPadding.vP),
                const Text(
                  '@ 2026 Voicera. All rights reserved.',
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    color: Colors.grey,
                    fontSize:12,
                  ),
                ),
                const SizedBox(height: AppPadding.vP),
                Row (
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    IconButton(
                      onPressed: () {},
                      icon: const Icon(Icons.facebook, color:Colors.grey),
                    ),
                    IconButton(
                      onPressed: () {},
                      icon: const Icon(Icons.share, color: Colors.grey),
                    )
                  ],)
              ]
            )

          ),
      ],),),
    );
  }
}

