import 'package:flutter/material.dart';

import '../features/home/home_screen.dart';
import 'theme/app_theme.dart';

class QipaishiApp extends StatelessWidget {
  const QipaishiApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Qipaishi',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light(),
      home: const HomeScreen(),
    );
  }
}

