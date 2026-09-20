/// Client-side mirror of the request limits enforced by the backend.
///
/// These values duplicate what `backend/models.py` declares through Pydantic and
/// what `risk_limits.py` bounds for the model. The duplication is unavoidable in
/// a hand-written contract, so every constant here names the backend rule it
/// mirrors: keep both sides in step when a bound changes.
///
/// Rationale: the UI should reject exactly what the backend rejects. A laxer
/// client turns a local validation message into an opaque 422 round trip.
class RiskLimits {
  const RiskLimits._();

  /// `returns`: 10 to 2000 finite values.
  static const int returnsMinCount = 10;
  static const int returnsMaxCount = 2000;

  /// `investment_amount`: strictly greater than zero.
  static const double investmentMinExclusive = 0;

  /// `var_confidence`: 0.8 inclusive, 1.0 exclusive.
  static const double varConfidenceMin = 0.8;
  static const double varConfidenceMaxExclusive = 1;

  /// `loss_threshold`: zero or greater.
  static const double lossThresholdMin = 0;

  /// `draws`: 500 to 10000 inclusive.
  static const int drawsMin = 500;
  static const int drawsMax = 10000;

  /// `tune`: 200 to 10000 inclusive.
  static const int tuneMin = 200;
  static const int tuneMax = 10000;

  /// `target_accept`: 0.5 to 0.99 inclusive.
  static const double targetAcceptMin = 0.5;
  static const double targetAcceptMax = 0.99;
}
