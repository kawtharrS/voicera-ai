import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:mobile/apis/auth_service.dart';

class AgentResponse {
  final String response;
  final String emotion;
  AgentResponse({required this.response, required this.emotion});
}

class AgentService {
  final String baseUrl;
  AgentService(this.baseUrl);
  Future<AgentResponse> ask(String question) async {
    final response = await http
        .post(
          Uri.parse('$baseUrl/api/ask-anything'),
          headers: AuthService.headers,
          body: jsonEncode({'question': question}),
        );
    if (response.statusCode != 200) {
      throw Exception('Agent Error (${response.statusCode}): ${response.body}');
    }
    final responseData = jsonDecode(response.body);
    final data = responseData['data'] ?? {};
        
    final agentResponse = AgentResponse(
      response: data['response'] ?? '',
      emotion: data['emotion'] ?? 'neutral',
    );
        
    return agentResponse;
  }
}