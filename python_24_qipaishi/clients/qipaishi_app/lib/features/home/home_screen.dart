import 'package:flutter/material.dart';

import '../../layouts/desktop/desktop_shell.dart';
import '../../layouts/mobile/mobile_shell.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        if (constraints.maxWidth >= 900) {
          return const DesktopShell();
        }
        return const MobileShell();
      },
    );
  }
}

