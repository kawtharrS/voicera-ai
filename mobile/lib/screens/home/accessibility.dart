import 'package:flutter/material.dart';

class AccessibilityIcon extends StatelessWidget{
  final IconData icon;
  final String label;
  
  const AccessibilityIcon({
    Key? key, 
    required this.icon,
    required this.label,
  }) : super(key: key);

  @override
  Widget build(BuildContext context)
  {
    return Column(children: [
      Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.grey[300],
          shape: BoxShape.circle,
        ),
        child: Icon(icon, size:32, color: Colors.grey[700]),
      ),
      const SizedBox(height: 16),
      Text(
        label, 
        style: const TextStyle(
          fontSize: 12,
          color: Colors.grey,
        ),
      ),
    ],);
  }
}