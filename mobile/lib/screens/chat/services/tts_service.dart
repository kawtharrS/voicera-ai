import 'package:just_audio/just_audio.dart';
import 'package:flutter/material.dart';
import 'audio_cache_service.dart';

class TtsService {
  final AudioPlayer _player;
  final String baseUrl;
  final AudioCacheService _cache = AudioCacheService();

  TtsService(this._player, this.baseUrl);

  Future<void> speak(String text, String voice) async {
    try {
      
      await _player.stop();
      if (_cache.isCached(text, voice)) {
        final cachedPath = _cache.getCachedFilePath(text, voice);
        if (cachedPath != null) {
          await _player.setFilePath(cachedPath);
          await _player.play();
          return;
        }
      }

      final filePath = await _cache.cacheAudio(text, voice);
      if (filePath != null) {
        await _player.setFilePath(filePath);
        await _player.play();
        return;
      }

      final url =
          '$baseUrl/api/tts?text=${Uri.encodeComponent(text)}&voice=${Uri.encodeComponent(voice)}';
      await _player.setAudioSource(AudioSource.uri(Uri.parse(url)), preload: true);
      await _player.play();
    } catch (e) {
      rethrow;
    }
  }

  Future<void> preGenerateCommonPhrases({String voice = 'alloy'}) async {
    await _cache.initialize();
    await _cache.preGenerateCommonPhrases(voice: voice);
  }

  Future<void> clearCache() async {
    await _cache.clearCache();
  }

  Map<String, dynamic> getCacheStats() {
    return _cache.getCacheStats();
  }

  Future<void> stop() => _player.stop();
}