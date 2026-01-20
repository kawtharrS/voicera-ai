import 'package:flutter/material.dart';

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
                backgroundColor: const Color(0xFFFF9500),
                shape: RoundedRectangleBorder(borderRadius:BorderRadius.circular(20), ),
              ),
            onPressed: () {},
            child: const Text('Sign Up')
            ),
            ),
            const SizedBox(width: 16),
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
              ),
            ],
          ),
        ),
      ],),),
    );
  }
}