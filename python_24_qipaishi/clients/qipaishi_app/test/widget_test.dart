import 'package:flutter_test/flutter_test.dart';
import 'package:qipaishi_app/app/app.dart';

void main() {
  testWidgets('renders app shell', (tester) async {
    await tester.pumpWidget(const QipaishiApp());

    expect(find.text('Qipaishi'), findsOneWidget);
  });
}

