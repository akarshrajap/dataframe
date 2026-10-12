"""
Generate a realistic, comprehensive workflow runs dataset for interactive telemetry visualization.
"""
import pandas as pd
import numpy as np

np.random.seed(42)

pipelines = ['backend-api', 'frontend-web', 'data-warehouse', 'ml-service', 'infra-ops']
workflows = {
    'backend-api': ['ci_unit_tests', 'security_scan', 'api_integration_tests', 'deploy_staging'],
    'frontend-web': ['lint_and_build', 'e2e_playwright', 'bundle_analysis', 'deploy_prod'],
    'data-warehouse': ['hourly_dbt_run', 'daily_etl_sync', 'schema_validation'],
    'ml-service': ['feature_pipeline', 'model_evaluation', 'drift_monitoring'],
    'infra-ops': ['terraform_plan', 'backup_snapshot', 'cert_renewal']
}
triggers = ['push', 'pull_request', 'schedule', 'workflow_dispatch']

records = []
base_time = pd.Timestamp('2026-10-10 00:00:00', tz='UTC')

for run_id in range(2001, 2081):
    pipe = np.random.choice(pipelines, p=[0.30, 0.25, 0.20, 0.15, 0.10])
    wf = np.random.choice(workflows[pipe])
    trig = np.random.choice(triggers, p=[0.40, 0.35, 0.15, 0.10])
    
    # Random time in a 4-day window
    offset_min = np.random.randint(0, 4 * 24 * 60)
    created_at = base_time + pd.Timedelta(minutes=offset_min)
    
    # Queue latency: 5s to 90s
    queue_sec = int(np.random.exponential(scale=25) + 5)
    started_at = created_at + pd.Timedelta(seconds=queue_sec)
    
    # Outcome probabilities
    r = np.random.rand()
    if r < 0.72:
        status = 'completed'
        conclusion = 'success'
        fail_reason = 'None'
    elif r < 0.88:
        status = 'completed'
        conclusion = 'failure'
        fail_reasons = [
            'TestAssertionError: auth_mock_failed',
            'CompilationError: typescript type mismatch',
            'DBLockTimeout: lock acquisition failed',
            'OutOfMemoryError: worker killed by OOM killer',
            'ConnectionRefused: redis host unreachable'
        ]
        fail_reason = np.random.choice(fail_reasons)
    elif r < 0.94:
        status = 'completed'
        conclusion = 'timed_out'
        fail_reason = 'TimeoutExceeded: max step execution exceeded'
    elif r < 0.98:
        status = 'completed'
        conclusion = 'cancelled'
        fail_reason = 'UserCancelled: aborted by author commit'
    else:
        status = 'in_progress'
        conclusion = np.nan
        fail_reason = 'None'

    # Duration depending on pipeline & conclusion
    if pipe == 'backend-api':
        dur = np.random.normal(loc=180, scale=40)
    elif pipe == 'frontend-web':
        dur = np.random.normal(loc=120, scale=30)
    elif pipe == 'data-warehouse':
        dur = np.random.normal(loc=1200, scale=250)
    elif pipe == 'ml-service':
        dur = np.random.normal(loc=1800, scale=400)
    else:
        dur = np.random.normal(loc=90, scale=20)
        
    dur = max(20, int(dur))
    if conclusion == 'timed_out':
        dur = 3600
        
    completed_at = started_at + pd.Timedelta(seconds=dur) if status == 'completed' else pd.NaT
    dur_sec = dur if status == 'completed' else np.nan
    
    # CPU & Memory metrics
    cpu = round(min(100.0, max(5.0, np.random.normal(loc=55, scale=20))), 1)
    mem = round(max(256.0, np.random.normal(loc=2048, scale=1024)), 1)
    
    records.append({
        'run_id': str(run_id),
        'pipeline': pipe,
        'workflow_name': wf,
        'trigger_event': trig,
        'status': status,
        'conclusion': conclusion if pd.notna(conclusion) else 'running',
        'created_at': created_at.isoformat(),
        'started_at': started_at.isoformat(),
        'completed_at': completed_at.isoformat() if pd.notna(completed_at) else None,
        'queue_latency_sec': queue_sec,
        'duration_sec': dur_sec,
        'cpu_utilization_pct': cpu,
        'memory_used_mb': mem,
        'failure_reason': fail_reason
    })

df = pd.DataFrame(records).sort_values(by='created_at').reset_index(drop=True)
df.to_csv('workflow_telemetry_runs.csv', index=False)
print(f"Generated workflow_telemetry_runs.csv with {len(df)} runs.")
