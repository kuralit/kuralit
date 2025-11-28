import 'dart:io' show Platform;
import 'package:flutter/foundation.dart' show kIsWeb;

/// Device and platform metadata collector
class MetadataCollector {
  /// SDK version
  static const String sdkVersion = '1.0.0';

  /// Collects platform information
  static String getPlatform() {
    if (kIsWeb) {
      return 'web';
    }
    if (Platform.isAndroid) {
      return 'android';
    }
    if (Platform.isIOS) {
      return 'ios';
    }
    if (Platform.isWindows) {
      return 'windows';
    }
    if (Platform.isMacOS) {
      return 'macos';
    }
    if (Platform.isLinux) {
      return 'linux';
    }
    return 'unknown';
  }

  /// Collects device information
  static Map<String, dynamic> getDeviceInfo() {
    final platform = getPlatform();
    final info = <String, dynamic>{
      'platform': platform,
      'sdkVersion': sdkVersion,
    };

    if (!kIsWeb) {
      try {
        if (Platform.isAndroid) {
          info['osVersion'] = Platform.operatingSystemVersion;
        } else if (Platform.isIOS) {
          info['osVersion'] = Platform.operatingSystemVersion;
        }
      } catch (e) {
        // Ignore errors in metadata collection
      }
    }

    return info;
  }

  /// Merges user metadata with device metadata
  static Map<String, dynamic> mergeMetadata({
    Map<String, dynamic>? userMetadata,
    Map<String, dynamic>? deviceMetadata,
  }) {
    final merged = <String, dynamic>{};

    // Add device metadata first
    if (deviceMetadata != null) {
      merged.addAll(deviceMetadata);
    }

    // Add default device info
    merged.addAll(getDeviceInfo());

    // Override with user metadata
    if (userMetadata != null) {
      merged.addAll(userMetadata);
    }

    return merged;
  }
}

