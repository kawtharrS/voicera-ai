import 'package:flutter/material.dart';
import 'screens/home.dart';
import 'screens/signIn.dart';
import 'screens/login.dart';
import 'screens/chat.dart';
void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Voicera',
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFFFF9500),
          brightness: Brightness.light,
        ),
      ),
      home: const HomePage(),
      routes: {
        '/signin': (context) => SignInPage(),
        '/login': (context) => LoginPage(),
        '/chat': (context) => VoiceChatPage(),
      },
    );
  }
}