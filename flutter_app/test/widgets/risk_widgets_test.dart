import 'package:analisis_riesgo_app/services/api_service.dart';
import 'package:analisis_riesgo_app/widgets/results_card.dart';
import 'package:analisis_riesgo_app/widgets/risk_form_fields.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

RiskResponse _buildResponse() {
  return RiskResponse(
    varValue: 50000,
    thresholdProbability: 0.05,
    investmentAmount: 1000000,
    varConfidence: 0.95,
    lossThreshold: 50000,
    parameterMeans: {
      'media_retorno': -0.001,
      'desviacion_retorno': 0.02,
    },
    histogramBase64: '',
  );
}

void main() {
  group('RiskFormFields', () {
    List<TextEditingController> controllers() => [
          TextEditingController(text: '1000000'),
          TextEditingController(text: '0.95'),
          TextEditingController(text: '50000'),
          TextEditingController(text: '2000'),
          TextEditingController(text: '1000'),
          TextEditingController(text: '0.9'),
        ];

    testWidgets('renders all six numeric fields', (WidgetTester tester) async {
      final c = controllers();
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: RiskFormFields(
              investmentController: c[0],
              varConfidenceController: c[1],
              thresholdController: c[2],
              drawsController: c[3],
              tuneController: c[4],
              targetAcceptController: c[5],
            ),
          ),
        ),
      );

      expect(find.text('Monto invertido'), findsOneWidget);
      expect(find.text('VaR (confianza)'), findsOneWidget);
      expect(find.text('Umbral de perdida'), findsOneWidget);
      expect(find.text('Iteraciones (draws)'), findsOneWidget);
      expect(find.text('Calentamiento (tune)'), findsOneWidget);
      expect(find.text('Target accept'), findsOneWidget);
      expect(find.byType(TextFormField), findsNWidgets(6));
    });

    testWidgets('validates non-numeric integer field', (WidgetTester tester) async {
      final c = controllers();
      final draws = TextEditingController(text: 'abc');
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: Form(
              child: RiskFormFields(
                investmentController: c[0],
                varConfidenceController: c[1],
                thresholdController: c[2],
                drawsController: draws,
                tuneController: c[4],
                targetAcceptController: c[5],
              ),
            ),
          ),
        ),
      );

      final form = tester.state(find.byType(Form)) as FormState;
      form.validate();
      await tester.pump();

      expect(find.text('Debe ser un numero entero'), findsOneWidget);
    });

    Future<void> validate(WidgetTester tester, List<TextEditingController> c,
        {TextEditingController? draws,
        TextEditingController? varConfidence}) async {
      final c2 = c;
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: Form(
              child: RiskFormFields(
                investmentController: c2[0],
                varConfidenceController: varConfidence ?? c2[1],
                thresholdController: c2[2],
                drawsController: draws ?? c2[3],
                tuneController: c2[4],
                targetAcceptController: c2[5],
              ),
            ),
          ),
        ),
      );

      final form = tester.state(find.byType(Form)) as FormState;
      form.validate();
      await tester.pump();
    }

    testWidgets('rejects draws above the backend maximum',
        (WidgetTester tester) async {
      await validate(tester, controllers(),
          draws: TextEditingController(text: '99999'));

      expect(find.text('Maximo 10000'), findsOneWidget);
    });

    testWidgets('rejects tune above the backend maximum',
        (WidgetTester tester) async {
      final c = controllers();
      c[4] = TextEditingController(text: '20000');

      await validate(tester, c);

      expect(find.text('Maximo 10000'), findsOneWidget);
    });

    testWidgets('rejects var confidence at the exclusive upper bound',
        (WidgetTester tester) async {
      await validate(tester, controllers(),
          varConfidence: TextEditingController(text: '1.0'));

      expect(find.text('Debe ser menor a 1.0'), findsOneWidget);
    });

    testWidgets('rejects the investment amount at the exclusive lower bound',
        (WidgetTester tester) async {
      final c = controllers();
      c[0] = TextEditingController(text: '0');

      await validate(tester, c);

      expect(find.text('Debe ser mayor a 0.0'), findsOneWidget);
    });

    // NaN compares false against every bound, so it needs its own guard.
    testWidgets('rejects non-finite double fields', (WidgetTester tester) async {
      await validate(tester, controllers(),
          varConfidence: TextEditingController(text: 'NaN'));

      expect(find.text('Debe ser un numero finito'), findsOneWidget);
    });
  });

  group('ResultsCard', () {
    testWidgets('renders summary and parameter cards', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(body: ResultsCard(response: _buildResponse())),
        ),
      );

      expect(find.text('Resumen de riesgo'), findsOneWidget);
      expect(find.text('Medias de parametros'), findsOneWidget);
      expect(find.text('media_retorno: -0.00100'), findsOneWidget);
      expect(find.text('desviacion_retorno: 0.02000'), findsOneWidget);
    });
  });
}