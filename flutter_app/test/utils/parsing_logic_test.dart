import 'package:flutter_test/flutter_test.dart';
import 'package:analisis_riesgo_app/utils/parsing_logic.dart';

void main() {
  group('Parsing Logic Tests', () {
    test('parseReturns parses valid comma-separated string', () {
      const input = '0.1, 0.2, -0.3';
      final result = parseReturns(input);
      expect(result, [0.1, 0.2, -0.3]);
    });

    test('parseReturns parses valid newline-separated string', () {
      const input = '0.1\n0.2\n-0.3';
      final result = parseReturns(input);
      expect(result, [0.1, 0.2, -0.3]);
    });

    test('parseReturns throws FormatException on empty input', () {
      expect(() => parseReturns(''), throwsFormatException);
    });

    test('parseReturns throws FormatException on invalid number', () {
      expect(() => parseReturns('0.1, abc'), throwsFormatException);
    });

    // double.tryParse accepts these spellings; the backend rejects them.
    test('parseReturns throws FormatException on NaN and Infinity', () {
      expect(() => parseReturns('0.1, NaN'), throwsFormatException);
      expect(() => parseReturns('0.1, Infinity'), throwsFormatException);
      expect(() => parseReturns('0.1, -Infinity'), throwsFormatException);
    });

    test('parseReturns accepts semicolons and mixed whitespace', () {
      expect(parseReturns('0.1;0.2\t-0.3'), [0.1, 0.2, -0.3]);
    });
  });
}
