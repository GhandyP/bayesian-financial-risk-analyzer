import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:analisis_riesgo_app/widgets/returns_input.dart';

void main() {
  testWidgets('ReturnsInputWidget renders correctly',
      (WidgetTester tester) async {
    final controller = TextEditingController();

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: ReturnsInputWidget(controller: controller),
        ),
      ),
    );

    expect(find.text('Retornos historicos'), findsOneWidget);
    expect(find.byType(TextFormField), findsOneWidget);
  });

  testWidgets('ReturnsInputWidget validates empty input',
      (WidgetTester tester) async {
    final controller = TextEditingController();

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: Form(
            child: ReturnsInputWidget(controller: controller),
          ),
        ),
      ),
    );

    final form = tester.state(find.byType(Form)) as FormState;
    form.validate();
    await tester.pump();

    expect(find.text('Debe ingresar retornos historicos.'), findsOneWidget);
  });
}
