import 'dart:convert';
import 'package:image_picker/image_picker.dart';
import 'package:http/http.dart' as http;
import 'package:mobile/apis/auth_service.dart';

class ImageDescribeService {
  final ImagePicker picker = ImagePicker();

  Future<String?> captureAndDescribe() async {
    final XFile? photo = await picker.pickImage(
      source: ImageSource.camera,
      imageQuality: 85,
    );

    if (photo == null) {
      return null;
    }

    final String baseUrl = AuthService.goBaseUrl;
    final uri = Uri.parse('$baseUrl/api/image/describe');
    final request = http.MultipartRequest('POST', uri);

    if (AuthService.token != null) {
      request.headers['Authorization'] = 'Bearer ${AuthService.token}';
    }

    request.files.add(await http.MultipartFile.fromPath(
      'file',
      photo.path,
    ));

    final streamed = await request.send().timeout(const Duration(minutes: 2));
    final response = await http.Response.fromStream(streamed).timeout(const Duration(minutes: 2));

    if (response.statusCode != 200) {
      throw Exception('Image describe error: ${response.statusCode} ${response.body}');
    }

    try {
      final responseData = jsonDecode(response.body) as Map<String, dynamic>;
      final data = responseData['data'] as Map<String, dynamic>? ?? {};
      final desc = data['description'] as String?;
      if (desc == null || desc.isEmpty) {
        return 'I could not understand what is in the image.';
      }
      return desc;
    } catch (e) {
      throw Exception('Failed to parse image description: $e');
    }
  }
}