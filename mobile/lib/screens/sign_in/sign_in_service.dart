import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:mobile/apis/auth_service.dart';
import 'package:flutter/material.dart';
import 'package:mobile/screens/sign_in/helper.dart';

class SignInService {
  static const String _signInEndpoint = '/api/register';

  static Future<void> signIn(
    BuildContext context,
    String name,
    String email,
    String password,
    String confirmPassword,
  ) async {
    name = name.trim();
    email = email.trim();
    password = password.trim();
    confirmPassword = confirmPassword.trim();

    if (name.isEmpty || email.isEmpty || password.isEmpty || confirmPassword.isEmpty) {
      showSnackBar(context, 'Please fill all fields');
      return;
    }

    if (!Validation.isValidEmail(email)) {
      showSnackBar(context, 'Please enter a valid email address');
      return;
    }

    if (password.length < 6) {
      showSnackBar(context, 'Password must be at least 6 characters');
      return;
    }

    if (password != confirmPassword) {
      showSnackBar(context, 'Passwords do not match');
      return;
    }

    try {
      final response = await http.post(
        Uri.parse('${AuthService.goBaseUrl}$_signInEndpoint'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'name': name,
          'email': email,
          'password': password,
          'confirmPassword': confirmPassword,
        }),
      ).timeout(
        const Duration(seconds: 10),
        onTimeout: () {
          throw Exception('Request timeout. Please try again.');
        },
      );

      final data = jsonDecode(response.body);

      if (!context.mounted) return;

      if (response.statusCode == 201 && data['ok'] == true) {
        AuthService.token = data['token'];
        showSnackBar(context, 'Registration successful!');

        if (context.mounted) {
          Navigator.pushReplacementNamed(context, '/login');
        }
      } else {
        final errorMessage = data['message'] ?? 'Registration failed. Please try again.';
        showSnackBar(context, errorMessage);
      }
    } on Exception catch (e) {
      showSnackBar(context, 'Error: ${e.toString()}');
    }
  }

  static void showSnackBar(BuildContext context, String message) {
    if (!context.mounted) return;

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        duration: const Duration(seconds: 3),
      ),
    );
  }
}