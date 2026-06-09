class SessionSnapshot {
  const SessionSnapshot({
    required this.accessToken,
    required this.tenantId,
  });

  final String? accessToken;
  final String? tenantId;

  bool get isAuthenticated => accessToken != null && accessToken!.isNotEmpty;
}

class SessionStore {
  SessionSnapshot _snapshot = const SessionSnapshot(
    accessToken: null,
    tenantId: null,
  );

  SessionSnapshot get snapshot => _snapshot;

  void update({
    required String accessToken,
    required String tenantId,
  }) {
    _snapshot = SessionSnapshot(
      accessToken: accessToken,
      tenantId: tenantId,
    );
  }

  void clear() {
    _snapshot = const SessionSnapshot(
      accessToken: null,
      tenantId: null,
    );
  }
}

