"""
Generate realistic workflow telemetry runs with branch, workflow, dates, and outcomes.
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
branches = ['main', 'develop', 'feature/auth-service', 'feature/ui-refresh', 'release/v2.1', 'hotfix/db-locks']
triggers = ['push', 'pull_request', 'schedule', 'workflow_dispatch']

records = []
base_time = pd.Timestamp('2026-10-05 00:00:00', tz='UTC')

for run_id in range(3001, 3121):
    pipe = np.random.choice(pipelines, p=[0.30, 0.25, 0.20, 0.15, 0.10])
    wf = np.random.choice(workflows[pipe])
    branch = np.random.choice(branches, p=[0.35, 0.25, 0.15, 0.10, 0.10, 0.05])
    trig = np.random.choice(triggers, p=[0.40, 0.35, 0.15, 0.10])
    
    # Random time in an 8-day window
    offset_min = np.random.randint(0, 8 * 24 * 60)
    created_at = base_time + pd.Timedelta(minutes=offset_min)
    
    # Queue latency: 4s to 90s
    queue_sec = int(np.random.exponential(scale=22) + 4)
    started_at = created_at + pd.Timedelta(seconds=queue_sec)
    
    # Outcome probabilities
    r = np.random.rand()
    if r < 0.74:
        status = 'completed'
        conclusion = 'success'
        fail_reason = 'None'
    elif r < 0.88:
        status = 'completed'
        conclusion = 'failure'
        fail_reasons = [
            'TestAssertionError: auth_mock_token_invalid',
            'CompilationError: typescript type mismatch in types.ts',
            'DBLockTimeout: lock acquisition failed on table users',
            'OutOfMemoryError: worker killed by OOM killer',
            'ConnectionRefused: redis host unreachable:6379'
        ]
        fail_reason = np.random.choice(fail_reasons)
    elif r < 0.94:
        status = 'completed'
        conclusion = 'timed_out'
        fail_reason = 'TimeoutExceeded: max step execution 3600s exceeded'
    elif r < 0.98:
        status = 'completed'
        conclusion = 'cancelled'
        fail_reason = 'UserCancelled: aborted by newer commit'
    else:
        status = 'in_progress'
        conclusion = 'running'
        fail_reason = 'None'

    # Durations based on pipeline
    if pipe == 'backend-api':
        dur = np.random.normal(loc=175, scale=35)
    elif pipe == 'frontend-web':
        dur = np.random.normal(loc=115, scale=25)
    elif pipe == 'data-warehouse':
        dur = np.random.normal(loc=1150, scale=220)
    elif pipe == 'ml-service':
        dur = np.random.normal(loc=1750, scale=350)
    else:
        dur = np.random.normal(loc=85, scale=18)
        
    dur = max(20, int(dur))
    if conclusion == 'timed_out':
        dur = 3600
        
    completed_at = started_at + pd.Timedelta(seconds=dur) if status == 'completed' else pd.NaT
    dur_sec = dur if status == 'completed' else np.nan
    
    cpu = round(min(100.0, max(5.0, np.random.normal(loc=56, scale=18))), 1)
    mem = round(max(256.0, np.random.normal(loc=2048, scale=950)), 1)
    commit_sha = f"{np.random.randint(0x1000000, 0xFFFFFFF):07x}"
    
    records.append({
        'run_id': str(run_id),
        'branch': branch,
        'commit_sha': commit_sha,
        'pipeline': pipe,
        'workflow_name': wf,
        'trigger_event': trig,
        'status': status,
        'conclusion': conclusion,
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
print(f"Generated workflow_telemetry_runs.csv with {len(df)} runs across {len(branches)} branches.")
