import 'package:flutter/material.dart';

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
        crossAxisAlignment: CrossAxisAlignment.center,
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

