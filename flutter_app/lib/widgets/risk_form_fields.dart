import 'package:flutter/material.dart';
import '../config/risk_limits.dart';

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
                    minExclusive: RiskLimits.investmentMinExclusive)),
            const SizedBox(width: 12),
            Expanded(
                child: _buildDoubleField(
                    'VaR (confianza)', varConfidenceController,
                    min: RiskLimits.varConfidenceMin,
                    maxExclusive: RiskLimits.varConfidenceMaxExclusive)),
          ],
        ),
        const SizedBox(height: 12),
        Row(
          children: [
            Expanded(
                child: _buildDoubleField(
                    'Umbral de perdida', thresholdController,
                    min: RiskLimits.lossThresholdMin)),
            const SizedBox(width: 12),
            Expanded(
                child: _buildIntegerField(
                    'Iteraciones (draws)', drawsController,
                    min: RiskLimits.drawsMin, max: RiskLimits.drawsMax)),
          ],
        ),
        const SizedBox(height: 12),
        Row(
          children: [
            Expanded(
                child: _buildIntegerField(
                    'Calentamiento (tune)', tuneController,
                    min: RiskLimits.tuneMin, max: RiskLimits.tuneMax)),
            const SizedBox(width: 12),
            Expanded(
                child: _buildDoubleField(
                    'Target accept', targetAcceptController,
                    min: RiskLimits.targetAcceptMin,
                    max: RiskLimits.targetAcceptMax)),
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

  /// Bounds mirror the backend constraints, including the strict ones: a value
  /// equal to an exclusive bound must be rejected here, not by the API.
  Widget _buildDoubleField(String label, TextEditingController controller,
      {double? min, double? minExclusive, double? max, double? maxExclusive}) {
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
        // NaN compares false against every bound below, so it must be rejected
        // explicitly or it would slip through to the request payload.
        if (!parsed.isFinite) {
          return 'Debe ser un numero finito';
        }
        if (min != null && parsed < min) {
          return 'Minimo $min';
        }
        if (minExclusive != null && parsed <= minExclusive) {
          return 'Debe ser mayor a $minExclusive';
        }
        if (max != null && parsed > max) {
          return 'Maximo $max';
        }
        if (maxExclusive != null && parsed >= maxExclusive) {
          return 'Debe ser menor a $maxExclusive';
        }
        return null;
      },
    );
  }
}
