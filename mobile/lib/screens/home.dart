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
                  backgroundColor: const Color(0xFFFF9500), 
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
              const SizedBox(height:20),
              Column(children: [
                ServiceCard(
                  color: const Color(0xFF4DB6AC),
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
                )
              ],),
            ]
          ))
      ],),),
    );
  }
}

class ServiceCard extends StatelessWidget{
  final Color color;
  final String title;
  final String description;
  final IconData icon;

  const ServiceCard({
    Key? key, 
    required this.color, 
    required this.title, 
    required this.description,
    required this.icon,
  }) : super(key: key);

  @override
  Widget build(BuildContext context){
    return Container(
      decoration: BoxDecoration(
        color: color, 
        borderRadius: BorderRadius.circular(12),
      ),
      padding: const EdgeInsets.all(24),
      width: double.infinity,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, color:Colors.white, size:32),
          const SizedBox(height:16),
          Text(
            title, 
            style: const TextStyle(
              color: Colors.white, 
              fontWeight: FontWeight.bold,
              fontSize: 14,
            ),
          ),
          const SizedBox(height: 16),
          Text(
            description,
            style: const TextStyle(
              color: Colors.white,
              fontSize:13,
              height:1.5,
            ),
          ),
        ],),
    );
  }
}