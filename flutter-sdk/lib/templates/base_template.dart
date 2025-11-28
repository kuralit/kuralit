import 'package:flutter/material.dart';

/// Base class for all Kuralit templates
/// 
/// Provides a common interface for template widgets that can be
/// used with the Kuralit SDK.
abstract class KuralitBaseTemplate extends StatefulWidget {
  /// The session ID for this template instance
  final String sessionId;

  const KuralitBaseTemplate({
    Key? key,
    required this.sessionId,
  }) : super(key: key);
}



