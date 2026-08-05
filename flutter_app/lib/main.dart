import 'package:flutter/material.dart';

import 'config/api_config.dart';
import 'services/api_service.dart';
import 'utils/parsing_logic.dart';
import 'widgets/loss_histogram.dart';

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
                Text(
                  'Introduce retornos historicos (como proporciones, p. ej. -0.012). Usa comas o saltos de linea.',
                  style: Theme.of(context).textTheme.bodyMedium,
                ),
                const SizedBox(height: 12),
                TextFormField(
                  controller: _returnsController,
                  minLines: 6,
                  maxLines: 14,
                  decoration: const InputDecoration(
                    labelText: 'Retornos historicos',
                    hintText: '-0.003, 0.012, -0.005',
                    border: OutlineInputBorder(),
                  ),
                  validator: (value) {
                    if (value == null || value.trim().isEmpty) {
                      return 'Debe ingresar retornos historicos.';
                    }
                    try {
                      final returns = parseReturns(value);
                      if (returns.length < 10) {
                        return 'Se requieren al menos 10 retornos.';
                      }
                    } catch (error) {
                      return error.toString();
                    }
                    return null;
                  },
                ),
                const SizedBox(height: 16),
                Row(
                  children: [
                    Expanded(child: _buildDoubleField('Monto invertido', _investmentController, min: 1)),
                    const SizedBox(width: 12),
                    Expanded(child: _buildDoubleField('VaR (confianza)', _varConfidenceController, min: 0.8, max: 0.999)),
                  ],
                ),
                const SizedBox(height: 12),
                Row(
                  children: [
                    Expanded(child: _buildDoubleField('Umbral de perdida', _thresholdController, min: 0)),
                    const SizedBox(width: 12),
                    Expanded(child: _buildIntegerField('Iteraciones (draws)', _drawsController, min: 500)),
                  ],
                ),
                const SizedBox(height: 12),
                Row(
                  children: [
                    Expanded(child: _buildIntegerField('Calentamiento (tune)', _tuneController, min: 200)),
                    const SizedBox(width: 12),
                    Expanded(child: _buildDoubleField('Target accept', _targetAcceptController, min: 0.5, max: 0.99)),
                  ],
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
                  _buildSummaryCard(_response!),
                  const SizedBox(height: 16),
                  _buildParametersCard(_response!),
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

  Widget _buildSummaryCard(RiskResponse response) {
    final textTheme = Theme.of(context).textTheme;
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Resumen de riesgo', style: textTheme.titleMedium),
            const SizedBox(height: 8),
            Text('VaR ${response.varConfidence.toStringAsFixed(2)}: ${response.varValue.toStringAsFixed(0)}'),
            Text('Prob. perdida >= ${response.lossThreshold.toStringAsFixed(0)}: '
                '${(response.thresholdProbability * 100).toStringAsFixed(2)} %'),
            Text('Monto invertido: ${response.investmentAmount.toStringAsFixed(0)}'),
          ],
        ),
      ),
    );
  }

  Widget _buildParametersCard(RiskResponse response) {
    final textTheme = Theme.of(context).textTheme;
    return Card(
      elevation: 1,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Medias de parametros', style: textTheme.titleMedium),
            const SizedBox(height: 8),
            for (final entry in response.parameterMeans.entries)
              Text('${entry.key}: ${entry.value.toStringAsFixed(5)}'),
          ],
        ),
      ),
    );
  }

  Widget _buildIntegerField(String label, TextEditingController controller, {int? min, int? max}) {
    return TextFormField(
      controller: controller,
      keyboardType: TextInputType.number,
      decoration: InputDecoration(labelText: label, border: const OutlineInputBorder()),
      validator: (value) {
        if (value == null || value.trim().isEmpty) {
          return 'Requerido';
        }
        final parsed = int.tryParse(value);
        if (parsed == null) {
          return 'Debe ser un numero entero';
        }
        if (min != null && parsed < min) {
          return 'Minimo $min';
        }
        if (max != null && parsed > max) {
          return 'Maximo $max';
        }
        return null;
      },
    );
  }

  Widget _buildDoubleField(String label, TextEditingController controller, {double? min, double? max}) {
    return TextFormField(
      controller: controller,
      keyboardType: const TextInputType.numberWithOptions(decimal: true),
      decoration: InputDecoration(labelText: label, border: const OutlineInputBorder()),
      validator: (value) {
        if (value == null || value.trim().isEmpty) {
          return 'Requerido';
        }
        final parsed = double.tryParse(value);
        if (parsed == null) {
          return 'Debe ser un numero';
        }
        if (min != null && parsed < min) {
          return 'Minimo $min';
        }
        if (max != null && parsed > max) {
          return 'Maximo $max';
        }
        return null;
      },
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
