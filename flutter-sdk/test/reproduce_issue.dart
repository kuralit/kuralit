import 'dart:convert';
import 'package:flutter_test/flutter_test.dart';
import 'package:kuralit_sdk/src/kuralit_protocol.dart';

void main() {
  group('ClientMessage Serialization', () {
    test('clientAudioChunk message format', () {
      final sessionId = 'test-session-id';
      final chunk = 'base64-encoded-data';
      final timestamp = 1234567890.123;

      final data = <String, dynamic>{
        'chunk': chunk,
        'timestamp': timestamp,
      };

      final message = ClientMessage(
        type: ClientMessageType.clientAudioChunk.toSnakeCase(),
        sessionId: sessionId,
        data: data,
        metadata: null,
      );

      final jsonString = message.toJsonString();
      print('JSON: $jsonString');

      final decoded = jsonDecode(jsonString);
      expect(decoded['type'], equals('client_audio_chunk'));
      expect(decoded['session_id'], equals(sessionId));
      expect(decoded['data']['chunk'], equals(chunk));
      expect(decoded['data']['timestamp'], equals(timestamp));
      expect(decoded.containsKey('metadata'), isFalse);
    });

    test('toSnakeCase conversion', () {
      expect(ClientMessageType.clientText.toSnakeCase(), equals('client_text'));
      expect(ClientMessageType.clientAudioStart.toSnakeCase(), equals('client_audio_start'));
      expect(ClientMessageType.clientAudioChunk.toSnakeCase(), equals('client_audio_chunk'));
      expect(ClientMessageType.clientAudioEnd.toSnakeCase(), equals('client_audio_end'));
    });
  });
}
