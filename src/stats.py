"""Transparent statistical methods for the synthetic sales analysis.

The forecast uses the Step 13-tested seasonal-naive baseline, which is allowed
by the TRD and meets the BR-03 error target on the Step 10 holdout. Step 8
mentions a moving average; mentor confirmation of this documented resolution
remains required. No advanced forecasting model is used.
"""

from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
from scipy import stats


_ALPHA = 0.05
_MIN_RELIABLE_N = 30


def _finite_values(values) -> np.ndarray:
    numeric = pd.to_numeric(pd.Series(values), errors="coerce").to_numpy(dtype=float)
    return numeric[np.isfinite(numeric)]


def _monthly_series(monthly) -> pd.Series:
    if isinstance(monthly, pd.DataFrame):
        if "revenue" not in monthly:
            raise ValueError("monthly DataFrame must contain a revenue column")
        if "sale_month" in monthly:
            index = pd.to_datetime(monthly["sale_month"], errors="coerce")
            values = monthly["revenue"]
        elif isinstance(monthly.index, pd.DatetimeIndex):
            index = pd.Series(monthly.index, index=monthly.index)
            values = monthly["revenue"]
        else:
            raise ValueError("monthly DataFrame needs sale_month or a DatetimeIndex")
        series = pd.Series(pd.to_numeric(values, errors="coerce").to_numpy(), index=index)
    elif isinstance(monthly, pd.Series):
        series = pd.to_numeric(monthly, errors="coerce").copy()
    else:
        raise TypeError("monthly must be a pandas Series or DataFrame")
    if not isinstance(series.index, pd.DatetimeIndex):
        try:
            series.index = pd.to_datetime(series.index, errors="coerce")
        except (TypeError, ValueError):
            raise ValueError("monthly index must contain calendar dates") from None
    valid = ~series.index.isna() & np.isfinite(series.to_numpy(dtype=float))
    series = series.iloc[np.flatnonzero(valid)]
    series.index = series.index.to_period("M").to_timestamp()
    if series.index.has_duplicates:
        series = series.groupby(level=0).sum()
    return series.sort_index()


def three_month_forecast(monthly, method="seasonal_naive") -> dict[str, object]:
    """Return three monthly estimates and last-three-month seasonal-naive MAPE."""
    if method != "seasonal_naive":
        raise ValueError("Only the documented 'seasonal_naive' method is supported")
    history = _monthly_series(monthly)
    if len(history) < 24:
        raise ValueError("At least 24 valid monthly observations are required")
    expected_index = pd.date_range(history.index.min(), history.index.max(), freq="MS")
    if not history.index.equals(expected_index):
        raise ValueError("Monthly history must be consecutive with no missing months")
    values = history.to_numpy(dtype=float)

    holdout_actual = values[-3:]
    holdout_prediction = values[-15:-12]
    nonzero = holdout_actual != 0
    mape_pct = (
        float(np.mean(np.abs(
            (holdout_actual[nonzero] - holdout_prediction[nonzero])
            / holdout_actual[nonzero]
        )) * 100)
        if nonzero.any()
        else float("nan")
    )
    forecast_values = values[-12:-9].tolist()
    last_month = history.index[-1]
    forecast_months = pd.date_range(
        last_month + pd.offsets.MonthBegin(1), periods=3, freq="MS"
    )
    return {
        "forecast_months": forecast_months,
        "forecast_values": forecast_values,
        "label": "Estimate",
        "method": "Seasonal naive (same calendar month in prior year)",
        "mape_pct": mape_pct,
    }


def welch_aov_test(a, b) -> dict[str, object]:
    """Compare two independent order-level AOV samples using Welch's t-test."""
    sample_a = _finite_values(a)
    sample_b = _finite_values(b)
    n_a, n_b = len(sample_a), len(sample_b)
    unreliable = n_a < _MIN_RELIABLE_N or n_b < _MIN_RELIABLE_N
    if n_a < 2 or n_b < 2:
        statistic = p_value = float("nan")
        effect_size = float("nan")
        verdict = "Insufficient data for a Welch t-test."
        interpretation = (
            "At least two valid observations are needed in each independent group; "
            "results are not reliable."
        )
    else:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            test = stats.ttest_ind(sample_a, sample_b, equal_var=False, nan_policy="omit")
        statistic = float(test.statistic)
        p_value = float(test.pvalue)
        pooled_scale = np.sqrt((np.var(sample_a, ddof=1) + np.var(sample_b, ddof=1)) / 2)
        effect_size = (
            float((np.mean(sample_a) - np.mean(sample_b)) / pooled_scale)
            if pooled_scale
            else (0.0 if np.mean(sample_a) == np.mean(sample_b) else float("inf"))
        )
        if not np.isfinite(p_value):
            verdict = "The test is undefined for these constant samples."
            interpretation = (
                "The data do not provide a defined Welch test result; "
                "statistical significance does not establish practical or causal importance."
            )
        elif p_value < _ALPHA:
            verdict = "Statistically significant difference at the 5% level."
            interpretation = (
                "The group means differ at the 5% level in this sample; this does not "
                "establish practical or causal importance."
            )
        else:
            verdict = "No statistically significant difference at the 5% level."
            interpretation = (
                "This sample does not show a 5%-level difference in group means; "
                "absence of significance does not prove equivalence."
            )
    return {
        "n_a": n_a,
        "n_b": n_b,
        "t_statistic": statistic,
        "p_value": p_value,
        "significant_5pct": bool(np.isfinite(p_value) and p_value < _ALPHA),
        "verdict": verdict,
        "interpretation": interpretation,
        "effect_size": effect_size,
        "unreliable": unreliable,
    }


def one_way_anova(groups) -> dict[str, object]:
    """Run a one-way ANOVA with sample sizes and explicit assumption diagnostics."""
    if not hasattr(groups, "items"):
        raise TypeError("groups must be a mapping of group names to observations")
    samples = {
        str(name): _finite_values(values)
        for name, values in groups.items()
    }
    group_sizes = {name: int(values.size) for name, values in samples.items()}
    usable = [values for values in samples.values() if values.size >= 2]
    unreliable = any(size < _MIN_RELIABLE_N for size in group_sizes.values())
    assumption_checks = {
        "independence": "Assumed from the group construction; not testable from these values.",
        "equal_variance": "Not assumed by the classic one-way ANOVA; Levene's test is reported.",
        "outlier_counts": {},
        "normality_p_values": {},
    }
    for name, sample in samples.items():
        if sample.size:
            first_quartile, third_quartile = np.quantile(sample, [0.25, 0.75])
            spread = third_quartile - first_quartile
            lower, upper = first_quartile - 1.5 * spread, third_quartile + 1.5 * spread
            assumption_checks["outlier_counts"][name] = int(
                ((sample < lower) | (sample > upper)).sum()
            )
        else:
            assumption_checks["outlier_counts"][name] = 0
        if sample.size >= 3:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                normality = (
                    stats.shapiro(sample)
                    if sample.size <= 5000
                    else stats.normaltest(sample)
                )
            assumption_checks["normality_p_values"][name] = float(normality.pvalue)
        else:
            assumption_checks["normality_p_values"][name] = float("nan")

    if len(samples) < 3 or len(usable) < 3 or len(usable) != len(samples):
        f_statistic = p_value = levene_p = float("nan")
        effect_size = float("nan")
        assumption_checks["equal_variance_p_value"] = levene_p
        verdict = "At least three groups with two valid observations each are required."
        interpretation = (
            "The ANOVA could not be calculated; gather adequate data for three or more groups."
        )
    else:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            result = stats.f_oneway(*usable)
            levene = stats.levene(*usable, center="median")
        f_statistic = float(result.statistic)
        p_value = float(result.pvalue)
        levene_p = float(levene.pvalue)
        all_values = np.concatenate(usable)
        grand_mean = float(np.mean(all_values))
        between_sum_squares = sum(
            values.size * (float(np.mean(values)) - grand_mean) ** 2
            for values in usable
        )
        total_sum_squares = float(np.sum((all_values - grand_mean) ** 2))
        effect_size = (
            between_sum_squares / total_sum_squares if total_sum_squares else 0.0
        )
        assumption_checks["equal_variance_p_value"] = levene_p
        assumption_checks["equal_variance_passed_5pct"] = bool(
            np.isfinite(levene_p) and levene_p >= _ALPHA
        )
        if not np.isfinite(p_value):
            verdict = "The ANOVA is undefined for these constant samples."
            interpretation = (
                "No defined F-test result is available; statistical significance does "
                "not establish practical or causal importance."
            )
        elif p_value < _ALPHA:
            verdict = "At least one group mean differs at the 5% level."
            interpretation = (
                "The sample provides evidence that at least one group mean differs; "
                "post-hoc testing is needed to identify which groups, and this is not causal evidence."
            )
        else:
            verdict = "No group-mean difference is significant at the 5% level."
            interpretation = (
                "This sample does not establish a difference among group means; "
                "non-significance does not prove equivalence."
            )
    return {
        "group_sizes": group_sizes,
        "f_statistic": f_statistic,
        "p_value": p_value,
        "effect_size_eta_squared": effect_size,
        "assumption_checks": assumption_checks,
        "interpretation": interpretation,
        "verdict": verdict,
        "significant_5pct": bool(np.isfinite(p_value) and p_value < _ALPHA),
        "unreliable": unreliable,
    }


def _correlation_strength(coefficient: float) -> str:
    magnitude = abs(coefficient)
    if magnitude < 0.1:
        return "negligible"
    if magnitude < 0.3:
        return "weak"
    if magnitude < 0.5:
        return "moderate"
    if magnitude < 0.7:
        return "strong"
    return "very strong"


def correlation_analysis(df: pd.DataFrame, method="pearson") -> pd.DataFrame:
    """Report discount/quantity/profit associations and explicitly reject causality."""
    method = str(method).lower()
    if method not in {"pearson", "spearman"}:
        raise ValueError("method must be 'pearson' or 'spearman'")
    candidate_pairs = (
        ("discount_pct", "quantity"),
        ("discount_pct", "profit"),
        ("quantity", "profit"),
    )
    output = []
    for variable_x, variable_y in candidate_pairs:
        if variable_x not in df or variable_y not in df:
            continue
        pair = pd.DataFrame(
            {
                variable_x: pd.to_numeric(df[variable_x], errors="coerce"),
                variable_y: pd.to_numeric(df[variable_y], errors="coerce"),
            }
        ).replace([np.inf, -np.inf], np.nan).dropna()
        n = len(pair)
        coefficient = p_value = float("nan")
        if n >= 2 and pair[variable_x].nunique() > 1 and pair[variable_y].nunique() > 1:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                result = (
                    stats.pearsonr(pair[variable_x], pair[variable_y])
                    if method == "pearson"
                    else stats.spearmanr(pair[variable_x], pair[variable_y])
                )
            coefficient = float(result.statistic)
            p_value = float(result.pvalue)
            strength = _correlation_strength(coefficient)
            direction = "positive" if coefficient > 0 else "negative"
            interpretation = (
                f"{strength.capitalize()} {direction} {method} association "
                f"(r={coefficient:.3f}, n={n}); correlation is not causation."
            )
        else:
            strength = "undefined"
            interpretation = (
                f"The {method} association is undefined for fewer than two valid "
                "observations or a constant variable; correlation is not causation."
            )
        output.append(
            {
                "variable_x": variable_x,
                "variable_y": variable_y,
                "pair": f"{variable_x} vs {variable_y}",
                "coefficient": coefficient,
                "p_value": p_value,
                "sample_size": n,
                "n": n,
                "strength": strength,
                "interpretation": interpretation,
                "method": method,
            }
        )
    return pd.DataFrame(
        output,
        columns=[
            "variable_x", "variable_y", "pair", "coefficient", "p_value",
            "sample_size", "n", "strength", "interpretation", "method",
        ],
    )
