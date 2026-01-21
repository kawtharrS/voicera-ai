import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:mobile/apis/auth_service.dart';

class AgentService {
  final String baseUrl;
  AgentService(this.baseUrl);

  Future<String> ask(String question) async {
    final response = await http
        .post(
          Uri.parse('$baseUrl/api/ask-anything'),
          headers: AuthService.headers,
          body: jsonEncode({'question': question}),
        )
        .timeout(const Duration(seconds: 30));

    if (response.statusCode != 200) {
      throw Exception('Agent Error (${response.statusCode}): ${response.body}');
    }
    final data = jsonDecode(response.body);
    return data['response'] ?? '';
  }
}