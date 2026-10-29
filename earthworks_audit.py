"""Audit average-end-area quantities on one alignment using explicit units."""
import argparse
import csv
import math
import sys
from auditlib import read_csv, number, unique, load_config, evidence, cell, write_reports

SECTIONS = ['station_m', 'cut_area_m2', 'fill_area_m2']
CLAIMS = ['from_m', 'to_m', 'claimed_cut_m3', 'claimed_fill_m3']
CONFIG = ['absolute_tolerance_m3', 'relative_tolerance', 'maximum_interval_m']


def audit(sections, claims, config):
    if len(sections) < 2:
        raise ValueError('at least two cross sections are required')
    abs_tol = number(config['absolute_tolerance_m3'], 'absolute tolerance', minimum=0)
    rel_tol = number(config['relative_tolerance'], 'relative tolerance', minimum=0)
    gap_max = number(config['maximum_interval_m'], 'maximum interval', positive=True)
    if rel_tol > 1:
        raise ValueError('relative_tolerance must be a fraction in [0, 1]')
    sections = [{k: number(r[k], k, minimum=None if k == 'station_m' else 0) for k in SECTIONS} for r in sections]
    if any(b['station_m'] <= a['station_m'] for a,b in zip(sections, sections[1:])):
        raise ValueError('stations must be strictly increasing; input is not silently sorted')
    claims = [{k: number(r[k], k, minimum=0 if k.startswith('claimed') else None) for k in CLAIMS} for r in claims]
    unique(claims, ['from_m', 'to_m'])
    if any(r['to_m'] <= r['from_m'] for r in claims):
        raise ValueError('claim to_m must exceed from_m')
    claim_map = {(r['from_m'], r['to_m']): r for r in claims}
    intervals = []
    for a,b in zip(sections, sections[1:]):
        start, end = a['station_m'], b['station_m']
        length = end - start
        result = {'from_m':start, 'to_m':end, 'findings':[]}
        if length > gap_max:
            result['findings'].append('INTERVAL_EXCEEDS_DEMO_LIMIT')
        claim = claim_map.pop((start, end), None)
        if claim is None:
            result['findings'].append('MISSING_CLAIM')
        for material in ['cut', 'fill']:
            volume = length * (a[f'{material}_area_m2'] + b[f'{material}_area_m2']) / 2
            number(volume, 'derived volume', minimum=0)
            result[f'{material}_m3'] = volume
            tolerance = max(abs_tol, rel_tol * volume)
            result[f'{material}_tolerance_m3'] = tolerance
            result[f'claimed_{material}_m3'] = None if claim is None else claim[f'claimed_{material}_m3']
            delta = None if claim is None else claim[f'claimed_{material}_m3'] - volume
            result[f'{material}_delta_m3'] = delta
            if delta is not None and abs(delta) > tolerance and not math.isclose(abs(delta), tolerance, rel_tol=1e-12, abs_tol=1e-12):
                result['findings'].append(f'{material.upper()}_DIFFERENCE_EXCEEDS_TOLERANCE')
        intervals.append(result)
    totals = {f'{m}_m3':sum(r[f'{m}_m3'] for r in intervals) for m in ['cut','fill']}
    totals['net_cut_minus_fill_m3'] = totals['cut_m3'] - totals['fill_m3']
    return {'demo':True, 'method':'average-end-area-v1', 'criteria':config, 'totals':totals,
            'intervals':intervals, 'unmatched_claims':list(claim_map.values()),
            'review_items':sum(bool(r['findings']) for r in intervals) + len(claim_map)}


def render(report):
    t = report['totals']
    lines = ['# Earthworks quantity audit', '', '**Synthetic demo — geometric volumes only.**', '',
             f"Calculated cut: **{t['cut_m3']:.2f} m³** · fill: **{t['fill_m3']:.2f} m³** · net cut minus fill: **{t['net_cut_minus_fill_m3']:.2f} m³**", '',
             '| Interval m | Cut m³ | Fill m³ | Claim minus calculated cut / fill m³ | Findings |',
             '|---|---:|---:|---|---|']
    for r in report['intervals']:
        delta = 'no claim' if r['cut_delta_m3'] is None else f"{r['cut_delta_m3']:.2f} / {r['fill_delta_m3']:.2f}"
        lines.append(f"| {r['from_m']:g}–{r['to_m']:g} | {r['cut_m3']:.2f} | {r['fill_m3']:.2f} | {delta} | {', '.join(r['findings']) or 'Within demo tolerance'} |")
    for r in report['unmatched_claims']:
        lines.append(f"\nUnmatched claim: {r['from_m']:g}–{r['to_m']:g} m; excluded from matched comparisons.")
    lines += ['', 'No shrink/swell, stripping, unsuitable material, haul balance or commercial entitlement is evaluated.', '']
    return '\n'.join(lines)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('sections')
    p.add_argument('claims')
    p.add_argument('--config', default='examples/demo_criteria.json')
    p.add_argument('--out', default='reports')
    p.add_argument('--fail-on-findings', action='store_true')
    a = p.parse_args()
    try:
        report = audit(read_csv(a.sections, SECTIONS), read_csv(a.claims, CLAIMS), load_config(a.config, CONFIG))
        report['inputs'] = evidence([a.sections, a.claims, a.config])
        write_reports(a.out, report, render(report))
    except (ValueError, OSError, csv.Error, OverflowError) as exc:
        print(f'Input/report error: {exc}', file=sys.stderr)
        return 2
    print(f"Audited {len(report['intervals'])} intervals; {report['review_items']} need review. Reports: {a.out}")
    return int(a.fail_on_findings and report['review_items'] > 0)


if __name__ == '__main__':
    sys.exit(main())
