import 'package:flutter/material.dart';
import '../config/risk_limits.dart';
import '../utils/parsing_logic.dart';

class ReturnsInputWidget extends StatelessWidget {
  const ReturnsInputWidget({
    super.key,
    required this.controller,
  });

  final TextEditingController controller;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Introduce retornos historicos (como proporciones, p. ej. -0.012). Usa comas o saltos de linea.',
          style: Theme.of(context).textTheme.bodyMedium,
        ),
        const SizedBox(height: 12),
        TextFormField(
          controller: controller,
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
              if (returns.length < RiskLimits.returnsMinCount) {
                return 'Se requieren al menos ${RiskLimits.returnsMinCount} retornos.';
              }
              if (returns.length > RiskLimits.returnsMaxCount) {
                return 'El maximo es ${RiskLimits.returnsMaxCount} retornos.';
              }
            } catch (error) {
              return error.toString();
            }
            return null;
          },
        ),
      ],
    );
  }
}
