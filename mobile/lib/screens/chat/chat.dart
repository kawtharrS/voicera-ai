import 'package:flutter/material.dart';
import 'package:flutter/semantics.dart';
import 'package:flutter/services.dart';
import 'package:mobile/constants/colors.dart';
import 'package:just_audio/just_audio.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:mobile/apis/auth_service.dart';


class VoiceChatPage extends StatefulWidget {
  const VoiceChatPage({Key? key}) : super(key: key);

  @override
  State<VoiceChatPage> createState() => VoiceChatState();
}

class VoiceChatState extends State<VoiceChatPage>
    with TickerProviderStateMixin {

  late AnimationController pulseController;
  late AnimationController waveController;
  late AudioPlayer audioPlayer;
  bool isRecording = false;
  bool isPlaying = false;
  String? baseUrl;
  String selectedVoice = 'alloy';
  final TextEditingController _textController = TextEditingController();
  bool isLoadingVoice = false;
  bool isLoadingAgent = false; 
  String _transcription = '';
  String? goBaseUrl; 



  final List<String> voices = ['alloy', 'echo', 'fable', 'onyx', 'nova', 'shimmer'];

  @override
  void initState() {
    super.initState();

    pulseController = AnimationController(
      duration: const Duration(milliseconds: 2000),
      vsync: this,
    )..repeat();

    waveController = AnimationController(
      duration: const Duration(milliseconds: 1500),
      vsync: this,
    )..repeat();

    audioPlayer = AudioPlayer();
    _initAudioPlayer();
    _loadBaseUrl();
  }

  void _initAudioPlayer() {
    audioPlayer.playerStateStream.listen((playerState) {
      if (mounted) {
        setState(() {
          isPlaying = playerState.playing;
        });
      }
    });

  }

  Future<void> _loadBaseUrl() async {
    baseUrl = AuthService.baseUrl; 
    goBaseUrl = AuthService.goBaseUrl; 
    _testConnection();
  }


  Future<void> _testConnection() async {
    if (baseUrl == null) return;
    
    try {
      final fastapiResp = await http.get(
        Uri.parse('$baseUrl/api/tts?text=test'),
        headers: AuthService.headers,
      ).timeout(const Duration(seconds: 3));
      debugPrint('FastAPI Success: ${fastapiResp.statusCode}');

      final goResp = await http.get(
        Uri.parse('$goBaseUrl/health'),
        headers: AuthService.headers,
      ).timeout(const Duration(seconds: 3));

      debugPrint('Go Backend Success: ${goResp.statusCode}');
    } catch (e) {
      debugPrint('Connection Failed: $e');
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Backend connection warning: $e'),
            backgroundColor: Colors.orange,
            duration: const Duration(seconds: 5),
          ),
        );
      }
    }
  }

  @override
  void dispose() {
    pulseController.dispose();
    waveController.dispose();
    audioPlayer.dispose();
    _textController.dispose();
    super.dispose();
  }


  Future<void> _toggleRecording() async {
    if (isRecording) {
      // Stopping recording - trigger agent if we have text
      setState(() => isRecording = false);
      _speakWithCustomTTS('Processing your question');
      
      final query = _textController.text.isNotEmpty 
          ? _textController.text 
          : 'Tell me something interesting';
          
      _sendToAgent(query);
    } else {
      // Starting recording
      setState(() => isRecording = true);
      _speakWithCustomTTS('Listening');
    }
  }

  Future<void> _sendToAgent(String text) async {
    if (goBaseUrl == null) return;

    try {
      debugPrint('Sending to Agent: $text');
      debugPrint('Using Headers: ${AuthService.headers}');
      
      final response = await http.post(
        Uri.parse('$goBaseUrl/api/ask-anything'),
        headers: AuthService.headers,
        body: jsonEncode({'question': text}),
      ).timeout(const Duration(seconds: 30));

      debugPrint('Agent Response Status: ${response.statusCode}');
      debugPrint('Agent Response Body: ${response.body}');

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final aiAnswer = data['response'] ?? 'I couldn\'t find an answer.';
        
        if (mounted) {
          setState(() {
            _transcription = aiAnswer;
            isLoadingAgent = false;
          });
        }

        // Automatically read the AI response aloud
        _speakWithCustomTTS(aiAnswer);
      } else {
        throw Exception('Agent error (${response.statusCode}): ${response.body}');
      }
    } catch (e) {
      debugPrint('Agent Error Details: $e');
      if (mounted) {
        setState(() => isLoadingAgent = false);
      }
      _speakWithCustomTTS('Sorry, I encountered an error connecting to the agent. $e');
    }

  }



  Future<void> _speakWithCustomTTS(String text) async {
    if (baseUrl == null || baseUrl!.isEmpty) {
      debugPrint('Base URL not configured');
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('TTS endpoint not configured')),
      );
      return;
    }

    try {
      if (mounted) setState(() => isLoadingVoice = true);
      
      if (audioPlayer.playing) {
        await audioPlayer.stop();
      }

      // Build TTS endpoint URL
      String ttsUrl = '$baseUrl/api/tts?text=${Uri.encodeComponent(text)}&voice=${Uri.encodeComponent(selectedVoice)}';
      debugPrint('Fetching TTS: $ttsUrl');

      // Use a more robust AudioSource for streaming
      await audioPlayer.setAudioSource(
        AudioSource.uri(Uri.parse(ttsUrl)),
        preload: true,
      );
      
      if (mounted) {
        setState(() {
          isLoadingVoice = false;
          isPlaying = true; // Set explicitly as well
        });
      }
      await audioPlayer.play();

    } catch (e) {
      debugPrint('TTS Error: $e');
      if (mounted) {
        setState(() {
          isPlaying = false;
          isLoadingVoice = false;
        });
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Voice Error: $e')),
        );
      }
    }
  }




  void _showVoiceSelector() {
    showDialog(
      context: context,
      builder: (BuildContext context) {
        return AlertDialog(
          title: const Text('Select Voice'),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: voices.map((voice) {
                return GestureDetector(
                  onLongPress: () => _speakWithCustomTTS('Voice option: $voice'),
                  child: ListTile(
                    title: Text(voice),
                    leading: Radio<String>(
                      value: voice,
                      groupValue: selectedVoice,
                      onChanged: (String? newValue) {
                        if (newValue != null) {
                          setState(() {
                            selectedVoice = newValue;
                          });
                          Navigator.pop(context);
                          // Voice reader feedback for selection
                          _speakWithCustomTTS('Selected $voice voice');
                        }
                      },
                    ),
                  ),
                );


              }).toList(),
            ),
          ),
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      body: SafeArea(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [

            Padding(
              padding: const EdgeInsets.all(16),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  IconButton(
                    icon: const Icon(Icons.arrow_back),
                    onPressed: () {
                      _speakWithCustomTTS('Go back');
                      Future.delayed(const Duration(milliseconds: 1000), () {
                        if (mounted) Navigator.pop(context);
                      });
                    },
                    tooltip: 'Go back',
                  ),


                  GestureDetector(
                    onLongPress: () => _speakWithCustomTTS('Voicera Voice Chat Title'),
                    child: const Text(
                      'Voicera Voice Chat',
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.more_vert),
                    onPressed: () {
                      _speakWithCustomTTS('Settings');
                      _showVoiceSelector();
                    },
                    tooltip: 'Select voice',
                  ),


                ],
              ),
            ),


            Expanded(
              child: Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [

                    Stack(
                      alignment: Alignment.center,
                      children: [

                        AnimatedBuilder(
                          animation: waveController,
                          builder: (context, child) {
                            return Container(
                              width: 220,
                              height: 220,
                              decoration: BoxDecoration(
                                shape: BoxShape.circle,
                                border: Border.all(
                                  color: AppColors.teal.withOpacity(
                                    isRecording
                                        ? 0.2 * (1 - waveController.value)
                                        : 0.05,
                                  ),
                                  width: 18,
                                ),
                              ),
                            );
                          },
                        ),

                        GestureDetector(
                          onTap: _toggleRecording,
                          onLongPress: () {

                            final String textToRead = _textController.text.isNotEmpty 
                                ? _textController.text 
                                : (isRecording
                                    ? 'Currently listening, please speak'
                                    : 'Press the circle to speak or type a message');
                            debugPrint('Long press detected for text: $textToRead');
                            _speakWithCustomTTS(textToRead);
                          },

                          child: Semantics(
                            button: true,
                            enabled: true,
                            onLongPress: () {
                              final String textToRead = _textController.text.isNotEmpty 
                                  ? _textController.text 
                                  : (isRecording ? 'Listening status' : 'Push to talk instructions');
                              debugPrint('Accessibility Long Press: $textToRead');
                              _speakWithCustomTTS(textToRead);
                            },
                            label: isRecording
                                ? 'Stop recording button'
                                : 'Voice orb. Tap to speak. Long press to read your message aloud.',
                            child: Container(
                              width: 180,
                              height: 180,
                              decoration: BoxDecoration(
                                shape: BoxShape.circle,
                                gradient: LinearGradient(
                                  begin: Alignment.topLeft,
                                  end: Alignment.bottomRight,
                                  colors: [
                                    AppColors.teal,
                                    isLoadingVoice ? Colors.teal : AppColors.teal.withOpacity(0.7),
                                  ],
                                ),
                                boxShadow: [
                                  BoxShadow(
                                    color: AppColors.teal.withOpacity(0.3),
                                    blurRadius: 20,
                                    spreadRadius: 5,
                                  ),
                                ],
                              ),
                              child: Center(
                                child: Column(
                                  mainAxisAlignment: MainAxisAlignment.center,
                                  children: [
                                    if (isLoadingVoice || isLoadingAgent)
                                      const CircularProgressIndicator(color: Colors.white, strokeWidth: 2),
                                    if (!isLoadingVoice && !isLoadingAgent)
                                      Text(
                                        isPlaying
                                            ? 'Speaking...'
                                            : (isRecording
                                                ? 'Listening...'
                                                : (isLoadingAgent ? 'Thinking...' : 'Tap to speak')),

                                        style: const TextStyle(
                                          color: Colors.white,
                                          fontSize: 14,
                                          fontWeight: FontWeight.w500,
                                        ),
                                      ),
                                  ],
                                ),
                              ),
                            ),
                          ),

                        ),

                      ],
                    ),
                    const SizedBox(height: 20),
                    Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 40),
                      child: GestureDetector(
                        behavior: HitTestBehavior.translucent,
                        onLongPress: () {
                          final text = _textController.text.isNotEmpty 
                              ? 'Your message is: ${_textController.text}' 
                              : 'Message input field is empty';
                          _speakWithCustomTTS(text);
                        },
                        child: TextField(
                        controller: _textController,
                        textAlign: TextAlign.center,
                        style: const TextStyle(
                          color: Colors.black87,
                          fontSize: 16,
                          fontWeight: FontWeight.w400,
                        ),
                        decoration: InputDecoration(
                          hintText: 'Type your message...',
                          hintStyle: const TextStyle(color: Colors.black26),
                          suffixIcon: _textController.text.isNotEmpty 
                            ? IconButton(
                                icon: Icon(
                                  isLoadingAgent ? Icons.hourglass_bottom : Icons.send, 
                                  color: AppColors.teal
                                ),
                                onPressed: () => _sendToAgent(_textController.text),
                              )
                            : null,

                          border: UnderlineInputBorder(

                            borderSide: BorderSide(color: AppColors.purple.withOpacity(0.3)),
                          ),
                          enabledBorder: UnderlineInputBorder(
                            borderSide: BorderSide(color: AppColors.purple.withOpacity(0.3)),
                          ),
                          focusedBorder: const UnderlineInputBorder(
                            borderSide: BorderSide(color: AppColors.purple),
                          ),
                        ),
                        onChanged: (val) {
                          setState(() {
                            _transcription = val;
                          });
                        },
                      ),
                    ),
                  ),
                    const SizedBox(height: 10),
                    GestureDetector(
                      onLongPress: () => _speakWithCustomTTS(
                        isRecording ? 'Status: Listening for your voice' : 'Instructions: Tap orb to speak or type message'
                      ),
                      child: Text(
                        isRecording
                            ? 'Listening for your voice...'
                            : 'Tap orb to speak or type above',
                        style: const TextStyle(
                          color: Colors.black54,
                          fontSize: 13,
                        ),
                      ),
                    ),

                    const SizedBox(height: 20),
                    // Status indicator
                    if (isPlaying)
                      GestureDetector(
                        onLongPress: () => _speakWithCustomTTS('Status: Speaking with $selectedVoice voice'),
                        child: Container(
                          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                          decoration: BoxDecoration(
                            color: AppColors.orange.withOpacity(0.1),
                            borderRadius: BorderRadius.circular(8),
                            border: Border.all(color: AppColors.orange),
                          ),
                          child: Text(
                            'Speaking with $selectedVoice voice...',
                            style: const TextStyle(
                              color: Colors.black87,
                              fontSize: 12,
                            ),
                          ),
                        ),
                      ),

                    if (!isPlaying && selectedVoice != 'alloy')
                      GestureDetector(
                        onLongPress: () => _speakWithCustomTTS('Status: Current voice is $selectedVoice'),
                        child: Container(
                          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                          decoration: BoxDecoration(
                            color: AppColors.teal.withOpacity(0.1),
                            borderRadius: BorderRadius.circular(8),
                            border: Border.all(color: AppColors.teal),
                          ),
                          child: Text(
                            'Current voice: $selectedVoice',
                            style: const TextStyle(
                              color: Colors.black87,
                              fontSize: 12,
                            ),
                          ),
                        ),
                      ),

                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}