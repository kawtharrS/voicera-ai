import 'package:flutter/material.dart';
import 'screens/home/home.dart';
import 'screens/sign_in/sign_in.dart';
import 'screens/login/login.dart';
import 'screens/chat/voice_chat.dart';
import 'theme/theme.dart';
import 'services/notification_service.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await NotificationService().init();
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'Voicera',
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(
          seedColor: AppColors.orange,
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