import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:mobile/apis/auth_service.dart';
import 'package:flutter/material.dart';

class LoginService {
  static const String loginEndpoint = '/api/login';

  static Future<void> login(
    BuildContext context,
    String emailText,
    String passwordText,
  ) async {
    emailText = emailText.trim();
    passwordText = passwordText.trim();

    if (emailText.isEmpty || passwordText.isEmpty) {
      _showSnackBar(context, 'Please enter email and password');
      return;
    }

    try {
      final response = await http.post(
        Uri.parse('${AuthService.goBaseUrl}$loginEndpoint'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'email': emailText,
          'password': passwordText,
        }),
      ).timeout(
        const Duration(seconds: 10),
        onTimeout: () {
          throw Exception('Request timeout. Please try again.');
        },
      );

      final data = jsonDecode(response.body);

      if (!context.mounted) return;

      if (response.statusCode == 200 && data['ok'] == true) {
        AuthService.token = data['token'];
        _showSnackBar(context, 'Login successful!');
        
        if (context.mounted) {
          Navigator.pushReplacementNamed(context, '/chat');
        }
      } else if (response.statusCode == 401) {
        _showSnackBar(context, 'Invalid email or password');
      } else if (response.statusCode == 404) {
        _showSnackBar(context, 'User not found');
      } else {
        final errorMessage = data['message'] ?? 'Login failed. Please try again.';
        _showSnackBar(context, errorMessage);
      }
    } on FormatException catch (_) {
      _showSnackBar(context, 'Invalid server response. Please try again.');
    } on Exception catch (e) {
      _showSnackBar(context, 'Error: ${e.toString()}');
    }
  }

  static void _showSnackBar(BuildContext context, String message) {
    if (!context.mounted) return;
    
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        duration: const Duration(seconds: 3),
      ),
    );
  }
}