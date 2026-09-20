import 'dart:convert';

import 'package:http/http.dart' as http;

class ConvergenceDiagnostics {
  ConvergenceDiagnostics({
    required this.maxRhat,
    required this.minEss,
    required this.divergences,
    required this.converged,
  });

  factory ConvergenceDiagnostics.fromJson(Map<String, dynamic> json) {
    return ConvergenceDiagnostics(
      maxRhat: (json['max_rhat'] as num).toDouble(),
      minEss: (json['min_ess'] as num).toDouble(),
      divergences: (json['divergences'] as num).toInt(),
      converged: json['converged'] as bool,
    );
  }

  final double maxRhat;
  final double minEss;
  final int divergences;
  final bool converged;
}

class RiskResponse {
  RiskResponse({
    required this.varValue,
    required this.varValueLower,
    required this.varValueUpper,
    required this.expectedShortfall,
    required this.thresholdProbability,
    required this.investmentAmount,
    required this.varConfidence,
    required this.lossThreshold,
    required this.parameterMeans,
    required this.histogramBase64,
    required this.diagnostics,
  });

  factory RiskResponse.fromJson(Map<String, dynamic> json) {
    return RiskResponse(
      varValue: (json['var_value'] as num).toDouble(),
      varValueLower: (json['var_value_lower'] as num).toDouble(),
      varValueUpper: (json['var_value_upper'] as num).toDouble(),
      expectedShortfall: (json['expected_shortfall'] as num).toDouble(),
      thresholdProbability: (json['threshold_probability'] as num).toDouble(),
      investmentAmount: (json['investment_amount'] as num).toDouble(),
      varConfidence: (json['var_confidence'] as num).toDouble(),
      lossThreshold: (json['loss_threshold'] as num).toDouble(),
      parameterMeans: (json['parameter_means'] as Map<String, dynamic>)
          .map((key, value) => MapEntry(key, (value as num).toDouble())),
      histogramBase64: json['histogram_base64'] as String,
      diagnostics: ConvergenceDiagnostics.fromJson(
          json['diagnostics'] as Map<String, dynamic>),
    );
  }

  final double varValue;
  final double varValueLower;
  final double varValueUpper;
  final double expectedShortfall;
  final double thresholdProbability;
  final double investmentAmount;
  final double varConfidence;
  final double lossThreshold;
  final Map<String, double> parameterMeans;
  final String histogramBase64;
  final ConvergenceDiagnostics diagnostics;
}

class ApiService {
  ApiService({required this.baseUrl, http.Client? client})
      : _client = client ?? http.Client();

  final String baseUrl;
  final http.Client _client;

  Future<RiskResponse> analyse({
    required List<double> returns,
    double investmentAmount = 1000000,
    double varConfidence = 0.95,
    double lossThreshold = 50000,
    int draws = 2000,
    int tune = 1000,
    double targetAccept = 0.9,
  }) async {
    final uri = Uri.parse('$baseUrl/analyse');

    final payload = <String, dynamic>{
      'returns': returns,
      'investment_amount': investmentAmount,
      'var_confidence': varConfidence,
      'loss_threshold': lossThreshold,
      'draws': draws,
      'tune': tune,
      'target_accept': targetAccept,
    };

    final response = await _client.post(
      uri,
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(payload),
    );

    if (response.statusCode >= 400) {
      throw Exception(
          'Error del backend: ${_extractErrorMessage(response.body)}');
    }

    return RiskResponse.fromJson(
        jsonDecode(response.body) as Map<String, dynamic>);
  }

  String _extractErrorMessage(String body) {
    try {
      final decoded = jsonDecode(body) as Map<String, dynamic>;
      final detail = decoded['detail'];
      if (detail is String) {
        return detail;
      }
      if (detail is List) {
        // FastAPI answers request validation failures with 422 and a list of
        // Pydantic error objects, which is the shape the UI used to print raw.
        final messages = _formatValidationErrors(detail);
        if (messages.isNotEmpty) {
          return messages;
        }
      }
      if (detail is Map<String, dynamic> && detail['detail'] != null) {
        return detail['detail'].toString();
      }
    } catch (_) {}
    return body.isEmpty ? 'Respuesta vacia del servidor.' : body;
  }

  /// Renders ``[{loc: [body, draws], msg: ...}]`` as one readable line per error.
  String _formatValidationErrors(List<dynamic> errors) {
    final lines = <String>[];
    for (final error in errors) {
      if (error is! Map<String, dynamic>) {
        continue;
      }
      final message = error['msg'];
      if (message is! String) {
        continue;
      }
      final field = _fieldFromLocation(error['loc']);
      lines.add(field == null ? message : '$field: $message');
    }
    return lines.join('\n');
  }

  /// ``loc`` is a path such as ``[body, draws]``; the field name is its tail.
  String? _fieldFromLocation(Object? loc) {
    if (loc is! List || loc.isEmpty) {
      return null;
    }
    final parts = loc
        .where((part) => part is String && part != 'body')
        .toList(growable: false);
    if (parts.isEmpty) {
      return null;
    }
    return parts.join('.');
  }
}
