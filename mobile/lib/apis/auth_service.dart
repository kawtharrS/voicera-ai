import 'dart:convert';

import 'package:http/http.dart' as http;

class UserInfo {
  final int id;
  final String email;
  final int roleId;

  UserInfo({
    required this.id,
    required this.email,
    required this.roleId,
  });

  factory UserInfo.fromJson(Map<String, dynamic> json) {
    int parseInt(dynamic value) {
      if (value is int) return value;
      if (value is String) return int.tryParse(value) ?? 0;
      return 0;
    }

    return UserInfo(
      id: parseInt(json['id']),
      email: (json['email'] ?? '') as String,
      roleId: parseInt(json['role_id']),
    );
  }
}

/// Simple helper for authentication-related API calls.
class AuthService {
  /// Bearer token for authenticated requests.
  static String? token;

  /// Base URL for the main backend.
  static String baseUrl = 'http://192.168.0.107:8000';

  /// Base URL for the Go agent backend.
  static String goBaseUrl = 'http://192.168.0.107:8080';

  /// Default headers used for all HTTP requests.
  static Map<String, String> get headers {
    return {
      'Content-Type': 'application/json',
      if (token != null) 'Authorization': 'Bearer $token',
    };
  }

  /// Fetches the currently logged-in user.
  ///
  /// Returns null if the request fails or the user is not logged in.
  static Future<UserInfo?> fetchCurrentUser() async {
    try {
      final uri = Uri.parse('$goBaseUrl/api/user');
      final response = await http.get(uri, headers: headers).timeout(
        const Duration(seconds: 10),
      );

      if (response.statusCode != 200) {
        return null;
      }

      final data = jsonDecode(response.body) as Map<String, dynamic>;
      return UserInfo.fromJson(data);
    } catch (_) {
      return null;
    }
  }
}
