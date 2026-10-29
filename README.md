# Earthworks Quantity Audit

**Reconcile a quantity schedule against cross-section areas, interval by interval.**

This demo calculates separate cut and fill quantities, matches claimed intervals, and highlights
missing entries and differences outside an explicit tolerance. It keeps a small discrepancy from
being hidden inside a project total.

**Portfolio demo · synthetic data · Python · numerical reconciliation**

## Try the example

```sh
python3 earthworks_audit.py examples/sections.csv examples/claimed_quantities.csv --out reports
```

The supplied fixture calculates **500 m³ cut** and **320 m³ fill**, with geometric net cut minus
fill of **180 m³**. The 20–40 m interval has a claimed cut quantity of 210 m³ against a calculated
200 m³: a +10 m³ difference, exceeding its 4 m³ demo tolerance.
[Read the generated example](examples/expected/report.md).

## Method

For each pair of adjacent sections: `V = L × (A1 + A2) / 2`.
Apply the formula separately to cut and fill areas, then sum the interval volumes.
The 0–20 m cut interval is `20 × (10 + 14) / 2 = 240 m³`.

A discrepancy is flagged when `abs(claim − calculated) > max(absolute tolerance, relative tolerance × calculated)`.
The supplied values are 1 m³ and 0.02 (2%), with a 25 m maximum interval review trigger.
Floating-point equality at the tolerance boundary uses a numerical epsilon of 1e-12; this does
not represent an engineering allowance. Negative deltas mean the claim is below the calculation.

## Input contract

| File | Required columns |
|---|---|
| Section areas | `station_m`, `cut_area_m2`, `fill_area_m2` |
| Quantity schedule | `from_m`, `to_m`, `claimed_cut_m3`, `claimed_fill_m3` |

Use one alignment and one consistent metre datum for chainage per run. Stations must be strictly
increasing; the script never silently sorts them. Areas and quantities cannot be negative.
`0+020` is not accepted: use `20`. Claim endpoints must numerically equal adjacent section
stations; no fuzzy matching is performed. Both `0` and `0.0` identify the same endpoint.

Duplicate claim intervals are rejected. Missing claims and unmatched claims are reported;
unmatched claims are excluded from comparisons, not silently added to geometric totals.

## Engineering boundaries

This is an average-end-area audit, not a TIN surface volume engine or bill certification.
It does not infer cross-section areas from drawings. Sparse sections, curvature, rapid terrain
changes, overlapping corridors and mixed datums need engineering review. Cut and fill are
geometric volumes; shrink/swell, compaction, material suitability and stripping are excluded.
A positive net cut does not establish usable surplus or a haul plan.

The next useful extension is an approved import mapping from a CAD quantity export plus a
separate, explicit material-factor schedule. An AI explanation layer could summarize discrepancies;
the arithmetic and tolerance rules should remain inspectable.

## Reference

[FHWA Earthwork Design](https://highways.dot.gov/federal-lands/pddm/dpg/earthwork-design)
describes average-end-area computation and its approximation limits, including potential curvature
corrections. This demo applies the simple formula and does not implement the whole design guidance.

## Trust and reproducibility

All included data is synthetic. This is an AI-assisted portfolio demo, not an employment project
or production system. See [provenance](PROVENANCE.md) and the [MIT license](LICENSE).
Input hashes in `report.json` identify the exact files used. Examples are deterministic and run offline.
The code uses Python's standard library; no API key, paid service or additional package is needed.

Run from this repository's folder using Python 3.9 or newer. The supplied version was locally tested
on Python 3.9.6. A GitHub Actions workflow is included for Python 3.11 and 3.13; hosted runs are not
claimed until the repository is uploaded and those checks run.

```sh
python3 -m unittest discover -s tests -v
```

On Windows, use `py -3` in place of `python3`. On systems where Python 3 is named `python`, use that.
Output folders contain `report.md` for reading and `report.json` for further analysis.
Normal execution returns 0 after generating a report; `--fail-on-findings` returns 1 when review is
needed. Invalid input or an output error returns 2. Required CSV cells must be nonblank, numbers
must be finite, and duplicate identifiers are rejected. Extra CSV columns are ignored.

## Explain it in an interview

Walk through one input, show a deliberate error, explain the result, and describe what the tool
cannot establish. The value is a reproducible review process with visible assumptions.
Do not claim production use, savings, compliance approval or independent authorship of AI-assisted work.
