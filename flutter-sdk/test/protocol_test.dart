import 'package:flutter_test/flutter_test.dart';
import 'package:kuralit_sdk/src/kuralit_protocol.dart';

void main() {
  group('Message Protocol', () {
    test('should create and serialize client message', () {
      final message = ClientMessage(
        type: ClientMessageType.clientText.name,
        sessionId: 'test-session',
        data: {'text': 'Hello'},
      );

      final json = message.toJson();
      expect(json['type'], equals('client_text'));
      expect(json['session_id'], equals('test-session'));
      expect(json['data']['text'], equals('Hello'));
    });

    test('should parse server message from JSON', () {
      final json = {
        'type': 'server_text',
        'session_id': 'test-session',
        'data': {'text': 'Hello'},
      };

      final message = ServerMessage.fromJson(json);
      expect(message.type, equals('server_text'));
      expect(message.sessionId, equals('test-session'));
      expect(message.data['text'], equals('Hello'));
    });

    test('should validate text message size', () {
      expect(MessageValidator.isValidTextSize('x' * 4096), isTrue);
      expect(MessageValidator.isValidTextSize('x' * 4097), isFalse);
    });

    test('should validate session ID', () {
      expect(MessageValidator.isValidSessionId('valid-session'), isTrue);
      expect(MessageValidator.isValidSessionId(''), isFalse);
    });
  });
}

