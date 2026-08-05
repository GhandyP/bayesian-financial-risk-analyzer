List<double> parseReturns(String raw) {
  final tokens = raw.split(RegExp(r'[\s,;]+'))
    ..removeWhere((token) => token.trim().isEmpty);
  if (tokens.isEmpty) {
    throw const FormatException('Debe ingresar retornos historicos.');
  }

  final values = <double>[];
  for (final token in tokens) {
    final parsed = double.tryParse(token);
    if (parsed == null) {
      throw FormatException('Valor invalido en retornos: "$token"');
    }
    values.add(parsed);
  }
  return values;
}
