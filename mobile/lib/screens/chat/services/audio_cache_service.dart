import 'dart:io';
import 'package:flutter/material.dart';
import 'package:path_provider/path_provider.dart';
import 'package:http/http.dart' as http;
import 'package:mobile/apis/auth_service.dart';

class AudioCacheService {
  static final AudioCacheService instance = AudioCacheService._internal();
  factory AudioCacheService() => instance;
  AudioCacheService._internal();

  Directory? cacheDir;
  final Map<String, String> cachedFiles = {};
  bool isInitialized = false;

  static const List<String> commonPhrases = [
    'Go Back',
    'Select Voices',
    'alloy',
    'echo',
    'fable',
    'onyx',
    'nova',
    'shimmer',
    'Listening',
    'Processing your question',
    'Please say something or type a message',
    'Currently listening, please speak',
    'Press the circle to speak or type a message',
    'Selected alloy voice',
    'Selected echo voice',
    'Selected fable voice',
    'Selected onyx voice',
    'Selected nova voice',
    'Selected shimmer voice',
  ];

  Future<void> initialize() async {
    if (isInitialized) return;
    try {
      final appDir = await getApplicationDocumentsDirectory();
      cacheDir = Directory('${appDir.path}/audio_cache');
      if (!await cacheDir!.exists()) {
        await cacheDir!.create(recursive: true);
      }
      await loadExistingCache();
      isInitialized = true;
    } catch (e) {
      rethrow;
    }
  }

  Future<void> loadExistingCache() async {
    if (cacheDir == null) return;
    final files = cacheDir!.listSync();
    for (final file in files) {
      if (file is File && file.path.endsWith('.mp3')) {
        final fileName = file.path.split(Platform.pathSeparator).last;
        final key = fileName.replaceAll('.mp3', '').replaceAll('_', ' ');
        cachedFiles[_getCacheKey(key, 'alloy')] = file.path;
      }
    }
  }

  String _getCacheKey(String text, String voice) {
    return '${text.toLowerCase()}_$voice';
  }

  String _getFileName(String text, String voice) {
    final sanitized = text
        .toLowerCase()
        .replaceAll(RegExp(r'[^\w\s]'), '')
        .replaceAll(RegExp(r'\s+'), '_');
    return '${sanitized}_$voice.mp3';
  }

  bool isCached(String text, String voice) {
    final key = _getCacheKey(text, voice);
    return cachedFiles.containsKey(key) && File(cachedFiles[key]!).existsSync();
  }

  String? getCachedFilePath(String text, String voice) {
    final key = _getCacheKey(text, voice);
    if (isCached(text, voice)) {
      return cachedFiles[key];
    }
    return null;
  }

  Future<String?> cacheAudio(String text, String voice) async {
    try {
      if (cacheDir == null) {
        await initialize();
      }

      final key = _getCacheKey(text, voice);

      if (isCached(text, voice)) {
        return cachedFiles[key];
      }

      final baseUrl = AuthService.baseUrl;

      final url =
          '$baseUrl/api/tts?text=${Uri.encodeComponent(text)}&voice=${Uri.encodeComponent(voice)}';
      final response = await http.get(
        Uri.parse(url),
        headers: AuthService.headers,
      );

      if (response.statusCode == 200) {
        final fileName = _getFileName(text, voice);
        final filePath = '${cacheDir!.path}/$fileName';
        final file = File(filePath);

        await file.writeAsBytes(response.bodyBytes);
        cachedFiles[key] = filePath;
        return filePath;
      }
      return null;
    } catch (e) {
      return null;
    }
  }

  Future<void> preGenerateCommonPhrases({String voice = 'alloy'}) async {
    if (!isInitialized) {
      await initialize();
    }
    for (final phrase in commonPhrases) {
      if (!isCached(phrase, voice)) {
        await cacheAudio(phrase, voice);
        await Future.delayed(const Duration(milliseconds: 100));
      }
    }
  }

  Future<void> clearCache() async {
    if (cacheDir != null && await cacheDir!.exists()) {
      await cacheDir!.delete(recursive: true);
      await cacheDir!.create(recursive: true);
      cachedFiles.clear();
      debugPrint('Cache cleared');
    }
  }

  Map<String, dynamic> getCacheStats() {
    return {
      'totalFiles': cachedFiles.length,
      'isInitialized': isInitialized,
      'cacheDirectory': cacheDir?.path,
    };
  }
}
