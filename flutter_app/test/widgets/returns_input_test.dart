import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:analisis_riesgo_app/config/risk_limits.dart';
import 'package:analisis_riesgo_app/widgets/returns_input.dart';

Future<void> _validateReturns(
    WidgetTester tester, TextEditingController controller) async {
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
}

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

  testWidgets('ReturnsInputWidget accepts a valid series',
      (WidgetTester tester) async {
    final controller = TextEditingController(
      text: List<String>.filled(10, '0.001').join(', '),
    );

    await _validateReturns(tester, controller);

    expect(find.text('Debe ingresar retornos historicos.'), findsNothing);
    expect(find.byType(TextFormField), findsOneWidget);
  });

  testWidgets('ReturnsInputWidget rejects fewer than the backend minimum',
      (WidgetTester tester) async {
    final controller = TextEditingController(
      text: List<String>.filled(9, '0.001').join(', '),
    );

    await _validateReturns(tester, controller);

    expect(find.text('Se requieren al menos 10 retornos.'), findsOneWidget);
  });

  testWidgets('ReturnsInputWidget rejects more than the backend maximum',
      (WidgetTester tester) async {
    final controller = TextEditingController(
      text: List<String>.filled(RiskLimits.returnsMaxCount + 1, '0.001')
          .join(', '),
    );

    await _validateReturns(tester, controller);

    expect(
      find.text('El maximo es ${RiskLimits.returnsMaxCount} retornos.'),
      findsOneWidget,
    );
  });

  testWidgets('ReturnsInputWidget rejects non-finite values',
      (WidgetTester tester) async {
    final controller = TextEditingController(text: 'NaN, 0.001, 0.002');

    await _validateReturns(tester, controller);

    expect(find.textContaining('Valor invalido en retornos'), findsOneWidget);
  });
}
