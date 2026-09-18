List<double> parseReturns(String raw) {
  final tokens = raw.split(RegExp(r'[\s,;]+'))
    ..removeWhere((token) => token.trim().isEmpty);
  if (tokens.isEmpty) {
    throw const FormatException('Debe ingresar retornos historicos.');
  }

  final values = <double>[];
  for (final token in tokens) {
    final parsed = double.tryParse(token);
    // `double.tryParse` accepts 'NaN' and 'Infinity', and those are exactly the
    // values the backend rejects (and that jsonEncode refuses to send), so they
    // are treated as invalid tokens here rather than one round trip later.
    if (parsed == null || !parsed.isFinite) {
      throw FormatException('Valor invalido en retornos: "$token"');
    }
    values.add(parsed);
  }
  return values;
}
