import 'dart:io' show Platform;
import 'package:flutter/foundation.dart' show kIsWeb;

/// Device and platform metadata collector
class MetadataCollector {
  /// SDK version
  static const String sdkVersion = '1.0.0';
  
  /// Current app state (foreground/background)
  static String _appState = 'foreground';
  
  /// Set app state (should be called by app lifecycle observer)
  static void setAppState(String state) {
    _appState = state;
  }
  
  /// Get current app state
  static String getAppState() => _appState;

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
  
  /// Gets detailed platform string for UI display
  static String getPlatformString() {
    if (kIsWeb) {
      return 'Web';
    }
    try {
      final osVersion = Platform.operatingSystemVersion;
      final platform = getPlatform();
      
      if (Platform.isIOS) {
        // Extract iOS version (e.g., "iPhone OS 17.2.1" -> "iOS 17.2.1")
        final match = RegExp(r'(\d+\.\d+(?:\.\d+)?)').firstMatch(osVersion);
        final version = match?.group(1) ?? 'Unknown';
        return 'iOS $version';
      } else if (Platform.isAndroid) {
        // Android version (e.g., "Android 13 (API 33)")
        final match = RegExp(r'(\d+(?:\.\d+)?)').firstMatch(osVersion);
        final version = match?.group(1) ?? 'Unknown';
        return 'Android $version';
      } else {
        return '${platform[0].toUpperCase()}${platform.substring(1)} $osVersion';
      }
    } catch (e) {
      return getPlatform();
    }
  }

  /// Collects device information
  static Map<String, dynamic> getDeviceInfo() {
    final platform = getPlatform();
    final info = <String, dynamic>{
      'platform': platform,
      'platform_string': getPlatformString(),
      'sdkVersion': sdkVersion,
      'app_state': _appState,
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
  
  /// Collects enhanced device information (with optional packages)
  /// This method can be extended to use device_info_plus, battery_plus, etc.
  static Future<Map<String, dynamic>> getEnhancedDeviceInfo() async {
    final baseInfo = getDeviceInfo();
    final enhanced = Map<String, dynamic>.from(baseInfo);
    
    // Try to get device model (requires device_info_plus package)
    try {
      // This would require: import 'package:device_info_plus/device_info_plus.dart';
      // For now, we'll add placeholders that can be filled by optional packages
      enhanced['device_model'] = 'Unknown';
      enhanced['device_brand'] = 'Unknown';
    } catch (e) {
      // Ignore if device_info_plus is not available
    }
    
    // Try to get battery level (requires battery_plus package)
    try {
      // This would require: import 'package:battery_plus/battery_plus.dart';
      enhanced['battery_level'] = null; // Will be null if package not available
    } catch (e) {
      // Ignore if battery_plus is not available
    }
    
    // Try to get network status (requires connectivity_plus package)
    try {
      // This would require: import 'package:connectivity_plus/connectivity_plus.dart';
      enhanced['network_type'] = 'unknown';
    } catch (e) {
      // Ignore if connectivity_plus is not available
    }
    
    // Try to get app version (requires package_info_plus package)
    try {
      // This would require: import 'package:package_info_plus/package_info_plus.dart';
      enhanced['app_version'] = null;
      enhanced['app_build_number'] = null;
    } catch (e) {
      // Ignore if package_info_plus is not available
    }
    
    return enhanced;
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

