import 'dart:async';
import 'dart:typed_data';
import 'package:record/record.dart';
import 'package:permission_handler/permission_handler.dart';

/// Audio recording service for real-time audio streaming
/// 
/// Handles microphone permissions, audio recording, and streaming audio chunks
/// in the format required by the Kuralit WebSocket API.
class AudioRecorderService {
  final AudioRecorder _recorder = AudioRecorder();
  StreamSubscription<Uint8List>? _audioStreamSubscription;
  Timer? _audioReadTimer;
  String? _recordingPath;
  bool _isRecording = false;
  bool _hasPermission = false;

  /// Whether recording is currently active
  bool get isRecording => _isRecording;

  /// Whether microphone permission has been granted
  bool get hasPermission => _hasPermission;

  /// Stream of audio chunks (PCM16 format)
  final StreamController<Uint8List> _audioChunkController = StreamController<Uint8List>.broadcast();

  /// Stream of audio chunks
  Stream<Uint8List> get audioChunks => _audioChunkController.stream;

  /// Stream for audio stall events (silence detected)
  final StreamController<void> _audioStalledController = StreamController<void>.broadcast();
  Stream<void> get onAudioStalled => _audioStalledController.stream;

  /// Request microphone permission
  /// 
  /// Returns true if permission is granted, false otherwise
  Future<bool> requestPermission() async {
    final status = await Permission.microphone.request();
    _hasPermission = status.isGranted;
    return _hasPermission;
  }

  /// Check if microphone permission is granted
  Future<bool> checkPermission() async {
    final status = await Permission.microphone.status;
    _hasPermission = status.isGranted;
    return _hasPermission;
  }

  /// Start recording audio
  /// 
  /// [sampleRate] - Audio sample rate (default: 16000)
  /// [encoding] - Audio encoding (default: AudioEncoder.pcm16bits)
  /// 
  /// Returns true if recording started successfully, false otherwise
  Future<bool> startRecording({
    int sampleRate = 16000,
    AudioEncoder encoding = AudioEncoder.pcm16bits,
  }) async {
    if (_isRecording) return true;

    if (!_hasPermission) {
      if (!await requestPermission()) return false;
    }

    try {
      if (!await _recorder.hasPermission()) {
        _hasPermission = false;
        return false;
      }

      print('🎤 AudioRecorder: Starting stream with sampleRate=$sampleRate, encoding=$encoding');
      
      final stream = await _recorder.startStream(
        RecordConfig(
          encoder: encoding,
          sampleRate: sampleRate,
          numChannels: 1,
          autoGain: false,
          echoCancel: false,
          noiseSuppress: false,
        ),
      );

      _isRecording = true;
      print('🎤 AudioRecorder: Stream started');

      // Buffer for header detection and chunking
      List<int> _audioBuffer = [];
      bool _headerProcessed = false;
      const int _wavHeaderSize = 44;
      // Target chunk size (approx 0.1s - 0.2s of audio)
      // 16kHz * 2 bytes/sample * 0.125s = 4000 bytes
      const int _targetChunkSize = 4096; 
      int _consecutiveSilenceChunks = 0;

      _audioStreamSubscription = stream.listen(
        (audioData) {
          if (!_isRecording || _audioChunkController.isClosed) return;

          // Check for silence (pure zeros)
          bool isSilence = true;
          for (var byte in audioData) {
            if (byte != 0) {
              isSilence = false;
              break;
            }
          }
          
          if (isSilence) {
            _consecutiveSilenceChunks++;
            // 10 chunks * ~0.1s = 1 second of pure zeros
            if (_consecutiveSilenceChunks > 10) {
              print('⚠️ AudioRecorder: Audio stalled (pure silence detected)');
              _audioStalledController.add(null);
              _consecutiveSilenceChunks = 0; // Reset to avoid flooding
            }
          } else {
            _consecutiveSilenceChunks = 0;
          }

          // Check for WAV header in the first chunk(s)
          if (!_headerProcessed) {
            _audioBuffer.addAll(audioData);
            
            // Check if we have enough data to detect header
            if (_audioBuffer.length >= 4) {
              // Check for 'RIFF' signature
              if (_audioBuffer[0] == 0x52 && _audioBuffer[1] == 0x49 && 
                  _audioBuffer[2] == 0x46 && _audioBuffer[3] == 0x46) {
                
                print('⚠️ AudioRecorder: WAV Header detected! Stripping...');
                
                if (_audioBuffer.length >= _wavHeaderSize) {
                  // We have the full header, strip it
                  final rawData = _audioBuffer.sublist(_wavHeaderSize);
                  _audioBuffer = rawData; // Keep remainder in buffer
                  _headerProcessed = true;
                } else {
                  // Wait for more data to complete the header
                  return;
                }
              } else {
                // No header detected
                print('ℹ️ AudioRecorder: No WAV header detected, sending raw PCM');
                _headerProcessed = true;
              }
            } else {
              return; // Wait for more data
            }
          } else {
            // Header processed, just append to buffer
            _audioBuffer.addAll(audioData);
          }

          // Process buffer into chunks
          while (_audioBuffer.length >= _targetChunkSize) {
            final chunk = Uint8List.fromList(_audioBuffer.sublist(0, _targetChunkSize));
            _audioChunkController.add(chunk);
            _audioBuffer = _audioBuffer.sublist(_targetChunkSize);
          }
        },
        onError: (error) {
          print('🎤 AudioRecorder: Stream error: $error');
          if (!_audioChunkController.isClosed) {
            _audioChunkController.addError(error);
          }
        },
        cancelOnError: false,
      );

      return true;
    } catch (e) {
      print('❌ AudioRecorder: Error starting stream: $e');
      _isRecording = false;
      return false;
    }
  }

  /// Stop recording audio
  /// 
  /// Returns the final audio chunk if available, null otherwise
  Future<Uint8List?> stopRecording() async {
    if (!_isRecording) {
      return null;
    }

    try {
      _isRecording = false;
      await _audioStreamSubscription?.cancel();
      _audioStreamSubscription = null;
      _audioReadTimer?.cancel();
      _audioReadTimer = null;

      final path = await _recorder.stop();
      _recordingPath = path;
      
      // Note: The record package doesn't return the final chunk directly
      // You may need to read it from the file if needed
      // For now, we'll return null as the stream should have handled all chunks
      return null;
    } catch (e) {
      return null;
    }
  }

  /// Pause recording (if supported)
  Future<bool> pauseRecording() async {
    if (!_isRecording) {
      return false;
    }

    try {
      await _recorder.pause();
      return true;
    } catch (e) {
      return false;
    }
  }

  /// Resume recording (if supported)
  Future<bool> resumeRecording() async {
    if (!_isRecording) {
      return false;
    }

    try {
      await _recorder.resume();
      return true;
    } catch (e) {
      return false;
    }
  }

  /// Get current audio amplitude
  Future<Amplitude> getAmplitude() async {
    try {
      return await _recorder.getAmplitude();
    } catch (e) {
      return Amplitude(current: -160.0, max: -160.0);
    }
  }

  /// Dispose resources
  void dispose() {
    stopRecording();
    _audioChunkController.close();
    _recorder.dispose();
  }
}


