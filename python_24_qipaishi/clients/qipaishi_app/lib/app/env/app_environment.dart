enum AppFlavor {
  dev,
  staging,
  prod,
}

class AppEnvironment {
  const AppEnvironment({
    required this.flavor,
    required this.apiBaseUrl,
  });

  final AppFlavor flavor;
  final Uri apiBaseUrl;

  static final AppEnvironment dev = AppEnvironment(
    flavor: AppFlavor.dev,
    apiBaseUrl: Uri.parse('http://localhost:8000'),
  );
}

