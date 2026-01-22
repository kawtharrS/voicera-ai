import 'dart:io';
import 'package:flutter/material.dart';
import 'package:path_provider/path_provider.dart';
import 'package:http/http.dart' as http;
import 'package:mobile/apis/auth_service.dart';

class AudioCacheService {
  static final AudioCacheService _instance = AudioCacheService._internal();
  factory AudioCacheService() => _instance;
  AudioCacheService._internal();

  Directory? _cacheDir;
  final Map<String, String> _cachedFiles = {};
  bool _isInitialized = false;

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
    if (_isInitialized) return;
    try {
      final appDir = await getApplicationDocumentsDirectory();
      _cacheDir = Directory('${appDir.path}/audio_cache');
      if (!await _cacheDir!.exists()) {
        await _cacheDir!.create(recursive: true);
      }
      await _loadExistingCache();
      _isInitialized = true;
    } catch (e) {
      rethrow;
    }
  }

  Future<void> _loadExistingCache() async {
    if (_cacheDir == null) return;
    final files = _cacheDir!.listSync();
    for (final file in files) {
      if (file is File && file.path.endsWith('.mp3')) {
        final fileName = file.path.split(Platform.pathSeparator).last;
        final key = fileName.replaceAll('.mp3', '').replaceAll('_', ' ');
        _cachedFiles[_getCacheKey(key, 'alloy')] = file.path;
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
    return _cachedFiles.containsKey(key) && 
           File(_cachedFiles[key]!).existsSync();
  }

  String? getCachedFilePath(String text, String voice) {
    final key = _getCacheKey(text, voice);
    if (isCached(text, voice)) {
      return _cachedFiles[key];
    }
    return null;
  }

  Future<String?> cacheAudio(String text, String voice) async {
    try {
      if (_cacheDir == null) {
        await initialize();
      }

      final key = _getCacheKey(text, voice);
      
      if (isCached(text, voice)) {
        return _cachedFiles[key];
      }

      final baseUrl = AuthService.baseUrl;
      if (baseUrl == null) {
        return null;
      }

      final url = '$baseUrl/api/tts?text=${Uri.encodeComponent(text)}&voice=${Uri.encodeComponent(voice)}';
      final response = await http.get(
        Uri.parse(url),
        headers: AuthService.headers,
      );

      if (response.statusCode == 200) {
        final fileName = _getFileName(text, voice);
        final filePath = '${_cacheDir!.path}/$fileName';
        final file = File(filePath);
        
        await file.writeAsBytes(response.bodyBytes);
        _cachedFiles[key] = filePath;
        return filePath;
      }
    } catch (e) {
      return null;
    }
  }

  Future<void> preGenerateCommonPhrases({String voice = 'alloy'}) async {
    if (!_isInitialized) {
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
    if (_cacheDir != null && await _cacheDir!.exists()) {
      await _cacheDir!.delete(recursive: true);
      await _cacheDir!.create(recursive: true);
      _cachedFiles.clear();
      debugPrint('Cache cleared');
    }
    
  }

  Map<String, dynamic> getCacheStats() {
    return {
      'totalFiles': _cachedFiles.length,
      'isInitialized': _isInitialized,
      'cacheDirectory': _cacheDir?.path,
    };
  }
}
