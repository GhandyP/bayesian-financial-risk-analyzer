"""Limits shared by the API contract and the PyMC model.

The bound lives in its own module on purpose: the Pydantic request model needs
the value to reject oversized payloads early, and it must be able to import it
without pulling in PyMC and Matplotlib. Both layers then validate against the
same number instead of keeping two copies of it in sync by hand.
"""

from __future__ import annotations

# Bound the input before allocating model and posterior predictive work. The
# Bayesian model is compute-heavy, and a 2000-point series is well beyond what
# VaR estimation needs while still keeping the request body small.
MAX_RETURNS = 2000

# Minimum series length the analysis is willing to fit a posterior on.
MIN_RETURNS = 10
