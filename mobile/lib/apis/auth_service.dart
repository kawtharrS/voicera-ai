import 'package:flutter/material.dart';

class AuthService {
  static String? token;
  static String baseUrl = 'http://192.168.0.107:8000';
  static String goBaseUrl = 'http://192.168.0.107:8080';

  static Map<String, String> get headers {
    return {
      'Content-Type': 'application/json',
      if (token != null) 'Authorization': 'Bearer $token',
    };
  }
}
