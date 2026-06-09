import '../../app/env/app_environment.dart';

class ApiClient {
  ApiClient({
    AppEnvironment? environment,
  }) : environment = environment ?? AppEnvironment.dev;

  final AppEnvironment environment;

  Uri endpoint(String path) {
    final normalizedPath = path.startsWith('/') ? path : '/$path';
    return environment.apiBaseUrl.replace(path: normalizedPath);
  }
}

