import 'package:flutter/material.dart';
import '../services/api_service.dart';

class ResultsCard extends StatelessWidget {
  const ResultsCard({super.key, required this.response});

  final RiskResponse response;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        _buildSummaryCard(context, response),
        const SizedBox(height: 16),
        _buildParametersCard(context, response),
      ],
    );
  }

  Widget _buildSummaryCard(BuildContext context, RiskResponse response) {
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
            Text(
                'VaR ${response.varConfidence.toStringAsFixed(2)}: ${response.varValue.toStringAsFixed(0)}'),
            Text(
                'Prob. perdida >= ${response.lossThreshold.toStringAsFixed(0)}: '
                '${(response.thresholdProbability * 100).toStringAsFixed(2)} %'),
            Text(
                'Monto invertido: ${response.investmentAmount.toStringAsFixed(0)}'),
          ],
        ),
      ),
    );
  }

  Widget _buildParametersCard(BuildContext context, RiskResponse response) {
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
}
