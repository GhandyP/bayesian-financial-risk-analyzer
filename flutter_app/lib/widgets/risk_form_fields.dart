import 'package:flutter/material.dart';

class RiskFormFields extends StatelessWidget {
  const RiskFormFields({
    super.key,
    required this.investmentController,
    required this.varConfidenceController,
    required this.thresholdController,
    required this.drawsController,
    required this.tuneController,
    required this.targetAcceptController,
  });

  final TextEditingController investmentController;
  final TextEditingController varConfidenceController;
  final TextEditingController thresholdController;
  final TextEditingController drawsController;
  final TextEditingController tuneController;
  final TextEditingController targetAcceptController;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Row(
          children: [
            Expanded(
                child: _buildDoubleField(
                    'Monto invertido', investmentController,
                    min: 1)),
            const SizedBox(width: 12),
            Expanded(
                child: _buildDoubleField(
                    'VaR (confianza)', varConfidenceController,
                    min: 0.8, max: 0.999)),
          ],
        ),
        const SizedBox(height: 12),
        Row(
          children: [
            Expanded(
                child: _buildDoubleField(
                    'Umbral de perdida', thresholdController,
                    min: 0)),
            const SizedBox(width: 12),
            Expanded(
                child: _buildIntegerField(
                    'Iteraciones (draws)', drawsController,
                    min: 500)),
          ],
        ),
        const SizedBox(height: 12),
        Row(
          children: [
            Expanded(
                child: _buildIntegerField(
                    'Calentamiento (tune)', tuneController,
                    min: 200)),
            const SizedBox(width: 12),
            Expanded(
                child: _buildDoubleField(
                    'Target accept', targetAcceptController,
                    min: 0.5, max: 0.99)),
          ],
        ),
      ],
    );
  }

  Widget _buildIntegerField(String label, TextEditingController controller,
      {int? min, int? max}) {
    return TextFormField(
      controller: controller,
      keyboardType: TextInputType.number,
      decoration:
          InputDecoration(labelText: label, border: const OutlineInputBorder()),
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

  Widget _buildDoubleField(String label, TextEditingController controller,
      {double? min, double? max}) {
    return TextFormField(
      controller: controller,
      keyboardType: const TextInputType.numberWithOptions(decimal: true),
      decoration:
          InputDecoration(labelText: label, border: const OutlineInputBorder()),
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
}
