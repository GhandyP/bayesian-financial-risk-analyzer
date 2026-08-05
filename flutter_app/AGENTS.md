# FLUTTER APP KNOWLEDGE BASE

## OVERVIEW
Single-page Flutter client for risk analysis input + API call + result visualization.

## STRUCTURE
```text
flutter_app/
├── lib/main.dart
├── lib/services/api_service.dart
├── lib/utils/parsing_logic.dart
├── lib/widgets/
├── test/utils/parsing_logic_test.dart
├── test/widgets/returns_input_test.dart
└── analysis_options.yaml
```

## WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|
| App entry + page state | `lib/main.dart` | `RiskFormPage` drives submit/loading/error state |
| HTTP integration | `lib/services/api_service.dart` | Request payload + response decoding |
| Return parsing rules | `lib/utils/parsing_logic.dart` | Shared parser for comma/newline tokens |
| Input widget behavior | `lib/widgets/returns_input.dart` | Form field + validator text |
| Result rendering | `lib/widgets/results_card.dart` + `loss_histogram.dart` | Summary + base64 image rendering |
| Parser tests | `test/utils/parsing_logic_test.dart` | Covers valid/invalid tokenization |
| Widget tests | `test/widgets/returns_input_test.dart` | Basic render + empty validation |

## CONVENTIONS
- User-facing strings are Spanish; keep messages consistent with backend validation tone.
- API endpoint is expected at `${baseUrl}/analyse`; maintain request key names (`snake_case`).
- Keep business parsing logic in `lib/utils/`, not inline widget lambdas.
- Preserve `flutter_lints` baseline from `analysis_options.yaml`.

## ANTI-PATTERNS
- Hardcoding production URLs in UI state.
- Duplicating parse logic between widget and service layers.
- Expanding `main.dart` with new business logic instead of extracting to widgets/utils.
- Skipping `flutter analyze`/`flutter test` after UI changes.

## COMMANDS
```bash
cd flutter_app && flutter pub get
cd flutter_app && flutter analyze
cd flutter_app && flutter test
cd flutter_app && flutter run
```

## NOTES
- Android emulator requires `10.0.2.2` instead of `localhost` for backend access.
- Histogram display assumes backend returns valid base64 PNG; decoding failures fall back to text message.
