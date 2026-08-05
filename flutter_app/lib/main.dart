import 'package:flutter/material.dart';

import 'config/api_config.dart';
import 'services/api_service.dart';
import 'utils/parsing_logic.dart';
import 'widgets/loss_histogram.dart';
import 'widgets/results_card.dart';
import 'widgets/returns_input.dart';
import 'widgets/risk_form_fields.dart';

void main() {
  runApp(const AnalisisRiesgoApp());
}

class AnalisisRiesgoApp extends StatelessWidget {
  const AnalisisRiesgoApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Analisis de Riesgo PyMC',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.redAccent),
        useMaterial3: true,
      ),
      home: const RiskFormPage(),
    );
  }
}

class RiskFormPage extends StatefulWidget {
  const RiskFormPage({super.key});

  @override
  State<RiskFormPage> createState() => _RiskFormPageState();
}

class _RiskFormPageState extends State<RiskFormPage> {
  final _formKey = GlobalKey<FormState>();
  final _returnsController = TextEditingController(
    text: List.generate(40, (index) => (-0.001 + (index % 5 - 2) * 0.004).toStringAsFixed(4)).join(', '),
  );
  final _investmentController = TextEditingController(text: '1000000');
  final _varConfidenceController = TextEditingController(text: '0.95');
  final _thresholdController = TextEditingController(text: '50000');
  final _drawsController = TextEditingController(text: '2000');
  final _tuneController = TextEditingController(text: '1000');
  final _targetAcceptController = TextEditingController(text: '0.9');
  final ApiService _apiService = ApiService(baseUrl: apiBaseUrl);

  RiskResponse? _response;
  bool _isSubmitting = false;
  String? _errorMessage;

  @override
  void dispose() {
    _returnsController.dispose();
    _investmentController.dispose();
    _varConfidenceController.dispose();
    _thresholdController.dispose();
    _drawsController.dispose();
    _tuneController.dispose();
    _targetAcceptController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Analisis Bayesiano de Riesgo')),
      body: SafeArea(
        child: Form(
          key: _formKey,
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                ReturnsInputWidget(controller: _returnsController),
                const SizedBox(height: 16),
                RiskFormFields(
                  investmentController: _investmentController,
                  varConfidenceController: _varConfidenceController,
                  thresholdController: _thresholdController,
                  drawsController: _drawsController,
                  tuneController: _tuneController,
                  targetAcceptController: _targetAcceptController,
                ),
                const SizedBox(height: 24),
                FilledButton.icon(
                  onPressed: _isSubmitting ? null : _submit,
                  icon: _isSubmitting
                      ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2))
                      : const Icon(Icons.radar),
                  label: Text(_isSubmitting ? 'Calculando...' : 'Analizar riesgo'),
                ),
                const SizedBox(height: 16),
                if (_errorMessage != null)
                  Text(_errorMessage!, style: const TextStyle(color: Colors.redAccent)),
                if (_response != null) ...[
                  const SizedBox(height: 16),
                  ResultsCard(response: _response!),
                  const SizedBox(height: 24),
                  Text('Distribucion simulada de perdidas', style: Theme.of(context).textTheme.titleMedium),
                  const SizedBox(height: 8),
                  LossHistogram(base64Image: _response!.histogramBase64),
                ],
              ],
            ),
          ),
        ),
      ),
    );
  }

  Future<void> _submit() async {
    final isValid = _formKey.currentState?.validate() ?? false;
    if (!isValid) {
      return;
    }

    final returns = parseReturns(_returnsController.text);
    final investment = double.parse(_investmentController.text);
    final varConfidence = double.parse(_varConfidenceController.text);
    final threshold = double.parse(_thresholdController.text);
    final draws = int.parse(_drawsController.text);
    final tune = int.parse(_tuneController.text);
    final targetAccept = double.parse(_targetAcceptController.text);

    setState(() {
      _isSubmitting = true;
      _errorMessage = null;
    });

    try {
      final response = await _apiService.analyse(
        returns: returns,
        investmentAmount: investment,
        varConfidence: varConfidence,
        lossThreshold: threshold,
        draws: draws,
        tune: tune,
        targetAccept: targetAccept,
      );
      setState(() {
        _response = response;
      });
    } catch (error) {
      setState(() {
        _errorMessage = error.toString();
        _response = null;
      });
    } finally {
      if (mounted) {
        setState(() {
          _isSubmitting = false;
        });
      }
    }
  }
}