import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:image_picker/image_picker.dart';
import 'package:http/http.dart' as http;
import 'package:mobile/apis/auth_service.dart';

class ImageDescribeService {
  final ImagePicker _picker = ImagePicker();

  Future<String?> captureAndDescribe() async {
    final XFile? photo = await _picker.pickImage(
      source: ImageSource.camera,
      imageQuality: 85,
    );

    if (photo == null) {
      return null;
    }

    final String baseUrl = AuthService.goBaseUrl;
    final uri = Uri.parse('$baseUrl/api/image/describe');

    debugPrint('Sending image to: $uri');

    final request = http.MultipartRequest('POST', uri);

    if (AuthService.token != null) {
      request.headers['Authorization'] = 'Bearer ${AuthService.token}';
    }

    request.files.add(await http.MultipartFile.fromPath(
      'file',
      photo.path,
    ));

    final streamed = await request.send();
    final response = await http.Response.fromStream(streamed);

    debugPrint('Image describe response: '
        'status=${response.statusCode}, body=${response.body}');

    if (response.statusCode != 200) {
      debugPrint('Image describe failed: ${response.statusCode} - ${response.body}');
      throw Exception('Image describe error: ${response.statusCode} ${response.body}');
    }

    try {
      final responseData = jsonDecode(response.body) as Map<String, dynamic>;
      final data = responseData['data'] as Map<String, dynamic>? ?? {};
      final desc = data['description'] as String?;
      if (desc == null || desc.isEmpty) {
        debugPrint('Image description is empty or null');
        return 'I could not understand what is in the image.';
      }
      return desc;
    } catch (e) {
      throw Exception('Failed to parse image description: $e');
    }
  }
}