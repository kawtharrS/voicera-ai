import 'package:just_audio/just_audio.dart';
import 'dart:convert';
import 'package:flutter/material.dart';

class TtsService {
  final AudioPlayer _player;
  final String baseUrl;

  TtsService(this._player, this.baseUrl);

  Future<void> speak(String text, String voice) async {
    try {
      final url =
          '$baseUrl/api/tts?text=${Uri.encodeComponent(text)}&voice=${Uri.encodeComponent(voice)}';
      await _player.stop();
      await _player.setAudioSource(
        AudioSource.uri(Uri.parse(url)),
        preload: true,
      );
      await _player.play();
    } catch (e) {
      debugPrint('TTS Error: $e');
      rethrow;
    }
  }

  Future<void> stop() => _player.stop();
}