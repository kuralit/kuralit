import 'dart:typed_data';

/// Audio streaming helper class
/// 
/// This class helps manage audio streaming by chunking audio data
/// into appropriate sizes (20-100ms) and managing the audio stream lifecycle.
/// 
/// Note: Actual audio capture should be done using platform-specific packages
/// like `record` for Flutter. This class handles the chunking and sending logic.
class AudioStreamer {
  final String sessionId;
  final int sampleRate;
  final String encoding;
  final int chunkDurationMs;

  bool _isStreaming = false;

  /// Whether the stream is currently active
  bool get isStreaming => _isStreaming;

  /// Creates a new AudioStreamer
  /// 
  /// [sessionId] - Session ID for the audio stream
  /// [sampleRate] - Audio sample rate (default: 16000)
  /// [encoding] - Audio encoding (default: 'pcm16')
  /// [chunkDurationMs] - Duration of each chunk in milliseconds (default: 50ms)
  AudioStreamer({
    required this.sessionId,
    this.sampleRate = 16000,
    this.encoding = 'pcm16',
    this.chunkDurationMs = 50,
  }) : assert(sampleRate > 0, 'sampleRate must be > 0'),
       assert(chunkDurationMs > 0, 'chunkDurationMs must be > 0');

  /// Calculates the chunk size in bytes
  /// 
  /// For PCM16: sampleRate * channels * bytesPerSample * (durationMs / 1000)
  /// For 16kHz, mono, 16-bit PCM: 16000 * 1 * 2 * 0.05 = 1600 bytes per 50ms chunk
  /// For PCM8: sampleRate * channels * bytesPerSample * (durationMs / 1000)
  /// For 16kHz, mono, 8-bit PCM: 16000 * 1 * 1 * 0.05 = 800 bytes per 50ms chunk
  int get chunkSizeBytes {
    final encodingLower = encoding.toLowerCase();
    final bytesPerSample = encodingLower == 'pcm8' ? 1 : 2; // PCM8 = 1 byte, PCM16 = 2 bytes
    // Assuming mono (1 channel)
    return (sampleRate * 1 * bytesPerSample * chunkDurationMs / 1000)
        .round()
        .clamp(1, double.infinity)
        .toInt();
  }

  /// Validates audio format
  /// 
  /// Supported sample rates: 8000, 16000, 44100, 48000 Hz
  /// Supported encodings: PCM16, PCM8 (case-insensitive)
  static bool isValidFormat(int sampleRate, String encoding) {
    // Validate sample rate
    const supportedSampleRates = [8000, 16000, 44100, 48000];
    if (!supportedSampleRates.contains(sampleRate)) {
      return false;
    }
    
    // Validate encoding (case-insensitive)
    final encodingLower = encoding.toLowerCase();
    return encodingLower == 'pcm16' || encodingLower == 'pcm8';
  }

  /// Calculates chunk size for a specific encoding
  /// 
  /// [sampleRate] - Audio sample rate
  /// [encoding] - Audio encoding (PCM16 or PCM8)
  /// [chunkDurationMs] - Duration of chunk in milliseconds
  /// [channels] - Number of audio channels (default: 1 for mono)
  static int calculateChunkSize(
    int sampleRate,
    String encoding,
    int chunkDurationMs, {
    int channels = 1,
  }) {
    final encodingLower = encoding.toLowerCase();
    final bytesPerSample = encodingLower == 'pcm8' ? 1 : 2;
    return (sampleRate * channels * bytesPerSample * chunkDurationMs / 1000)
        .round()
        .clamp(1, double.infinity)
        .toInt();
  }

  /// Generates a Unix timestamp in seconds with milliseconds precision
  /// 
  /// Returns current time as a double (e.g., 1234567890.123)
  static double generateTimestamp() {
    return DateTime.now().millisecondsSinceEpoch / 1000.0;
  }

  /// Converts float samples to PCM16 ByteArray
  /// 
  /// [samples] - Float array of audio samples (normalized to -1.0 to 1.0)
  /// Returns PCM16 encoded ByteData
  static Uint8List floatToPCM16(List<double> samples) {
    final buffer = Uint8List(samples.length * 2);
    final byteData = buffer.buffer.asByteData();

    for (int i = 0; i < samples.length; i++) {
      final sample = samples[i].clamp(-1.0, 1.0);
      final pcmValue = (sample * 32767).round().clamp(-32768, 32767);
      byteData.setInt16(i * 2, pcmValue, Endian.little);
    }

    return buffer;
  }

  /// Converts short samples to PCM16 ByteArray
  /// 
  /// [samples] - Short array of audio samples
  /// Returns PCM16 encoded ByteData
  static Uint8List shortToPCM16(List<int> samples) {
    final buffer = Uint8List(samples.length * 2);
    final byteData = buffer.buffer.asByteData();

    for (int i = 0; i < samples.length; i++) {
      final sample = samples[i].clamp(-32768, 32767);
      byteData.setInt16(i * 2, sample, Endian.little);
    }

    return buffer;
  }

  /// Chunks audio data into appropriate sizes
  /// 
  /// [audioData] - Raw PCM audio data
  /// Returns list of audio chunks
  List<Uint8List> chunkAudio(Uint8List audioData) {
    if (audioData.isEmpty) {
      return [];
    }

    final chunks = <Uint8List>[];
    final chunkSize = chunkSizeBytes;

    if (audioData.length <= chunkSize) {
      chunks.add(audioData);
      return chunks;
    }

    int offset = 0;
    while (offset < audioData.length) {
      final remaining = audioData.length - offset;
      final currentChunkSize = chunkSize < remaining ? chunkSize : remaining;
      chunks.add(audioData.sublist(offset, offset + currentChunkSize));
      offset += currentChunkSize;
    }

    return chunks;
  }
}

