import 'package:flutter_test/flutter_test.dart';
import 'package:kuralit_sdk/kuralit.dart';

void main() {
  group('Kuralit SDK', () {
    tearDown(() {
      Kuralit.dispose();
    });

    test('should initialize with valid config', () {
      expect(() {
        Kuralit.init(
          KuralitConfig(
            serverUrl: 'wss://test.com/ws',
            apiKey: 'test-key',
            appId: 'test-app',
          ),
        );
      }, returnsNormally);
    });

    test('should throw error when not initialized', () {
      expect(() => Kuralit.connect(), throwsStateError);
      expect(() => Kuralit.sendText('session', 'text'), throwsStateError);
      expect(() => Kuralit.isConnected(), returnsNormally);
    });

    test('should generate session ID', () {
      final sessionId1 = Kuralit.generateSessionId();
      final sessionId2 = Kuralit.generateSessionId();
      
      expect(sessionId1, isNotEmpty);
      expect(sessionId2, isNotEmpty);
      expect(sessionId1, isNot(equals(sessionId2)));
    });

    test('should validate text message size', () {
      Kuralit.init(
        KuralitConfig(
          serverUrl: 'wss://test.com/ws',
          apiKey: 'test-key',
          appId: 'test-app',
        ),
      );

      // Valid text
      expect(() => Kuralit.sendText('session', 'Hello'), returnsNormally);

      // Empty text should throw
      expect(
        () => Kuralit.sendText('session', ''),
        throwsArgumentError,
      );

      // Text exceeding 4KB should throw
      final largeText = 'x' * 4097;
      expect(
        () => Kuralit.sendText('session', largeText),
        throwsArgumentError,
      );
    });
  });
}

