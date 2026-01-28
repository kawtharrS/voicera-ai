import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:image_picker/image_picker.dart';
import 'package:http/http.dart' as http;
import 'package:mobile/apis/auth_service.dart';

class ImageDescribeService {
  final ImagePicker _picker = ImagePicker();

  /// Captures an image from the camera, sends it to the Go backend
  /// `/api/image/describe` endpoint, and returns the description text.
  ///
  /// Returns `null` if the user cancels the camera.
  Future<String?> captureAndDescribe() async {
    final XFile? photo = await _picker.pickImage(
      source: ImageSource.camera,
      imageQuality: 85,
    );

    if (photo == null) {
      return null; // user cancelled
    }

    final String baseUrl = AuthService.goBaseUrl;
    final uri = Uri.parse('$baseUrl/api/image/describe');

    debugPrint('Sending image to: $uri');

    final request = http.MultipartRequest('POST', uri);

    // Only send auth header; let MultipartRequest set Content-Type with boundary.
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
      throw Exception('Image describe error: ${response.statusCode} ${response.body}');
    }

    final data = jsonDecode(response.body) as Map<String, dynamic>;
    final desc = data['description'] as String?;
    return desc ?? 'I could not understand what is in the image.';
  }
}
