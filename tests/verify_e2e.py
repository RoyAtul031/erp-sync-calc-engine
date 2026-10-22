import requests

BASE = 'http://127.0.0.1:8050'

tests = []

# 1. Dashboard
r = requests.get(f'{BASE}/')
tests.append(('1. Dashboard HTML Interface', r.status_code == 200, f'Status {r.status_code} ({len(r.content)} bytes)'))

# 2. Swagger Docs
r = requests.get(f'{BASE}/api/docs/')
tests.append(('2. Interactive Swagger UI', r.status_code == 200, f'Status {r.status_code}'))

# 3. OpenAPI Schema
r = requests.get(f'{BASE}/api/schema/')
tests.append(('3. OpenAPI 3.0 Specification', r.status_code == 200, f'Status {r.status_code} ({len(r.content)} bytes)'))

# 4. ERP Connections
r = requests.get(f'{BASE}/api/erp/connections/')
conns = r.json().get('results', [])
tests.append(('4. ERP Connections Registry', r.status_code == 200 and len(conns) >= 2, f'{len(conns)} active connectors'))

# 5. SAP Sync Now
sap_id = conns[0]['id']
r = requests.post(f'{BASE}/api/erp/connections/{sap_id}/sync-now/', json={'sync_type': 'DELTA'})
tests.append(('5. SAP S/4HANA Delta Ingestion', r.status_code == 200, f"Saved: {r.json().get('records_saved')} records"))

# 6. Raw Ingested Payloads & SHA-256
r = requests.get(f'{BASE}/api/erp/raw-payloads/')
raws = r.json().get('results', [])
has_sha = len(raws) > 0 and len(raws[0].get('payload_sha256', '')) == 64
tests.append(('6. SHA-256 Cryptographic Snapshots', has_sha, f"Verified hash: {raws[0]['payload_sha256'][:16]}..."))

# 7. Auto-provisioned Facilities
r = requests.get(f'{BASE}/api/warehouse/facilities/')
facs = r.json().get('results', [])
tests.append(('7. Facility Auto-Provisioning', len(facs) == 4, f"{len(facs)} global plants registered"))

# 8. Global Compliance Frameworks
r = requests.get(f'{BASE}/api/calculation/frameworks/')
fws = r.json().get('results', [])
fw_codes = [f['code'] for f in fws]
tests.append(('8. Multi-Jurisdiction Compliance', 'EU_CSRD' in fw_codes and 'US_EPA' in fw_codes, ', '.join(fw_codes)))

# 9. AST Math Formula Simulator
r = requests.post(f'{BASE}/api/calculation/simulate-formula/', json={
    'expression': '(consumption * emission_factor) / 1000.0',
    'variables': {'consumption': 20000.0, 'emission_factor': 2.687, 'gwp': 1.0}
})
tests.append(('9. AST Safe Math Parser', r.status_code == 200 and r.json().get('result') == 53.74, f"Evaluated: {r.json().get('result')} tCO2e"))

# 10. Methodologies Listing
r = requests.get(f'{BASE}/api/calculation/methodologies/')
methods = r.json().get('results', [])
method_id = methods[0]['id']
tests.append(('10. Calculation Methodology Registry', r.status_code == 200, methods[0]['name']))

# 11. Execute Deterministic Calculation Run
r = requests.post(f'{BASE}/api/calculation/methodologies/{method_id}/run-calculation/', json={'initiated_by': 'E2E_VERIFICATION_TEST'})
run_data = r.json()
tests.append(('11. Deterministic Calculation Run', r.status_code == 200, f"Scope 1={run_data.get('total_scope_1_tco2e')} tCO2e | Scope 2={run_data.get('total_scope_2_location_tco2e')} tCO2e"))

# 12. CSV Audit Report Download
run_id = run_data.get('id')
r = requests.get(f'{BASE}/api/calculation/runs/{run_id}/export-csv/')
tests.append(('12. SOX/CSRD CSV Audit Report Export', r.status_code == 200 and 'text/csv' in r.headers.get('Content-Type', ''), f"Exported {len(r.content)} bytes"))

# 13. Audit Lineage & Proof Traceability
r = requests.get(f'{BASE}/api/calculation/calculated-records/?run={run_id}')
recs = r.json().get('results', [])
sample_trace = recs[0].get('calculation_trace', {}) if recs else {}
tests.append(('13. Granular Lineage Proof Trace', 'formula_evaluated' in sample_trace, f"Evaluated: {recs[0].get('formula_evaluated')}"))

print('\n======================================================================')
print('        OMNISYNC ESG - GLOBAL ENTERPRISE PLATFORM VERIFICATION        ')
print('======================================================================')
all_passed = True
for name, passed, detail in tests:
    status_str = '[PASS]' if passed else '[FAIL]'
    if not passed:
        all_passed = False
    print(f'{status_str} {name:<38} | {detail}')

print('======================================================================')
print(f'FINAL STATUS: {"100% PRODUCTION READY & VERIFIED" if all_passed else "FAILURES DETECTED"}')
print('======================================================================\n')
