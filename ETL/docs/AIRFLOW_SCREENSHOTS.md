# Airflow Screenshot Guide

This guide explains how to capture screenshots of your Airflow DAG runs for project submission.

---

## Required Screenshots

For a complete submission, capture these 6 essential views:

1. ✅ **DAG List View** - Shows all DAGs
2. ✅ **DAG Graph View** - Visual task dependencies
3. ✅ **DAG Tree View** - Historical runs timeline
4. ✅ **Task Instance Details** - Individual task execution
5. ✅ **Logs View** - Task execution logs
6. ✅ **Success Run** - Completed pipeline with green status

---

## Step-by-Step Screenshot Instructions

### 1️⃣ DAG List View

**Purpose**: Shows all available DAGs and their status

**Steps**:
1. Open Airflow UI: http://localhost:8080
2. Login with admin credentials
3. You'll see the DAGs list by default
4. Ensure `etl_pipeline` DAG is visible and enabled (toggle switch on left)
5. Capture screenshot showing:
   - DAG name (`etl_pipeline`)
   - Schedule interval
   - Last run status
   - Next run time

**What to include**:
- Full browser window
- DAG name clearly visible
- Status indicators (green = success, red = failed)

**Screenshot Name**: `01_dag_list_view.png`

---

### 2️⃣ DAG Graph View

**Purpose**: Visual representation of task dependencies

**Steps**:
1. Click on `etl_pipeline` DAG name
2. Click **Graph** tab at the top
3. You'll see a flowchart of tasks
4. Capture screenshot showing:
   - All tasks: `ingest_task`, `transform_task`, `load_task`, `validate_task`, `notify_task`
   - Task dependencies (arrows connecting tasks)
   - Color coding (green = success, red = failed, gray = not run)

**What to include**:
- Entire graph with all tasks visible
- Task names readable
- Dependency arrows clear

**Screenshot Name**: `02_dag_graph_view.png`

**Example Layout**:
```
ingest_task → transform_task → load_task → validate_task → notify_task
```

---

### 3️⃣ DAG Tree View

**Purpose**: Shows historical DAG runs over time

**Steps**:
1. While in `etl_pipeline` DAG details
2. Click **Tree** tab
3. You'll see a timeline of past runs
4. Capture screenshot showing:
   - Multiple run dates/times
   - Task status for each run (green squares = success)
   - Run duration

**What to include**:
- At least 2-3 recent runs visible
- Date/time stamps
- Success/failure patterns

**Screenshot Name**: `03_dag_tree_view.png`

---

### 4️⃣ Task Instance Details

**Purpose**: Shows detailed information about a single task execution

**Steps**:
1. In Graph or Tree view, click on any task (e.g., `transform_task`)
2. Click **Task Instance Details**
3. A modal/side panel opens
4. Capture screenshot showing:
   - Task ID
   - State (success/failed)
   - Start time
   - End time
   - Duration
   - Operator (PythonOperator)
   - Try number

**What to include**:
- Full task details panel
- All metadata visible

**Screenshot Name**: `04_task_instance_details.png`

---

### 5️⃣ Logs View

**Purpose**: Shows actual execution logs from a task

**Steps**:
1. Click on a task (e.g., `validate_task`)
2. Click **Log** button
3. Logs window opens showing execution output
4. Capture screenshot showing:
   - Log timestamp
   - Task output (print statements)
   - Success message or error traceback
   - Log level (INFO, WARNING, ERROR)

**What to include**:
- Key log messages showing task execution
- Quality metrics (if validate_task)
- Row counts
- File paths

**Screenshot Name**: `05_task_logs.png`

**Example Log Content**:
```
[2024-01-15 14:30:22] INFO - Starting validation task
[2024-01-15 14:30:23] INFO - Quality score: 85.5%
[2024-01-15 14:30:23] INFO - Null percentage: 5.2%
[2024-01-15 14:30:23] INFO - Duplicate percentage: 1.3%
[2024-01-15 14:30:23] INFO - Validation passed ✓
```

---

### 6️⃣ Success Run (Full Pipeline)

**Purpose**: Proves entire pipeline executed successfully

**Steps**:
1. Trigger a fresh DAG run: Click **Trigger DAG** (play button)
2. Wait for all tasks to complete (refresh page)
3. Once all tasks are green, capture:
   - Graph view with all green tasks
   - Run duration
   - Success timestamp

**What to include**:
- All 5 tasks showing green (success)
- Total pipeline duration
- Recent timestamp

**Screenshot Name**: `06_success_run.png`

---

## Bonus Screenshots (Optional but Recommended)

### 7️⃣ Gantt Chart View

**Purpose**: Shows task execution timeline and parallelism

**Steps**:
1. Click **Gantt** tab
2. Shows horizontal bars for each task
3. Capture to demonstrate execution timing

**Screenshot Name**: `07_gantt_chart.png`

---

### 8️⃣ Code View

**Purpose**: Shows DAG Python code directly in UI

**Steps**:
1. Click **Code** tab
2. Shows `etl_pipeline.py` source code
3. Capture to show DAG implementation

**Screenshot Name**: `08_code_view.png`

---

### 9️⃣ Audit Logs

**Purpose**: Shows database audit trail

**Steps**:
1. Open PostgreSQL client or Adminer
2. Query `ingest_audit` table:
```sql
SELECT run_id, table_name, rows_ingested, status, duration_seconds, created_at
FROM ingest_audit
ORDER BY created_at DESC
LIMIT 10;
```
3. Capture query results

**Screenshot Name**: `09_audit_logs.png`

---

### 🔟 Data Quality Dashboard

**Purpose**: Shows quality metrics from validation

**Steps**:
1. Open `data/quality_reports/` folder
2. Open latest HTML report in browser
3. Capture quality dashboard with charts

**Screenshot Name**: `10_quality_dashboard.png`

---

## How to Trigger Test Runs

### Trigger Manual Run

**From UI**:
1. Click play button (▶️) next to `etl_pipeline`
2. Optionally add run configuration JSON
3. Click **Trigger**

**From CLI**:
```powershell
airflow dags trigger etl_pipeline
```

**With Configuration**:
```powershell
airflow dags trigger etl_pipeline --conf '{"source": "test_run"}'
```

---

### Trigger Specific Task

To test a single task:

```powershell
# Test ingest task only
airflow tasks test etl_pipeline ingest_task 2024-01-15

# Test with actual execution (not test mode)
airflow dags test etl_pipeline 2024-01-15
```

---

## Intentional Failure (for Error Handling Demo)

To demonstrate error handling and alerts:

### Option 1: Modify Validation Threshold

Edit `dags/etl_pipeline.py`:
```python
# Temporarily set impossible threshold
quality_threshold = 99  # Changed from 80
```

Save, trigger DAG, and capture failed validation screenshot.

### Option 2: Disconnect Database

1. Stop PostgreSQL temporarily
2. Trigger DAG
3. Capture connection error in logs
4. Restart PostgreSQL

### Option 3: Corrupt Input File

1. Create empty CSV in `data/staging/`
2. Trigger DAG
3. Capture row count validation failure

**Screenshot Name**: `11_failure_example.png`

Then fix the issue and capture recovery:

**Screenshot Name**: `12_recovery_run.png`

---

## Screenshot Checklist

Before submission, ensure you have:

- [ ] `01_dag_list_view.png` - DAG overview
- [ ] `02_dag_graph_view.png` - Task dependencies
- [ ] `03_dag_tree_view.png` - Historical runs
- [ ] `04_task_instance_details.png` - Task metadata
- [ ] `05_task_logs.png` - Execution logs
- [ ] `06_success_run.png` - Full pipeline success
- [ ] (Optional) `07_gantt_chart.png` - Timing analysis
- [ ] (Optional) `08_code_view.png` - DAG source
- [ ] (Optional) `09_audit_logs.png` - Database audit
- [ ] (Optional) `10_quality_dashboard.png` - Quality metrics
- [ ] (Optional) `11_failure_example.png` - Error handling
- [ ] (Optional) `12_recovery_run.png` - Recovery

---

## Screenshot Best Practices

### ✅ DO:
- Use high resolution (1920x1080 or higher)
- Capture full browser window (not just content)
- Include timestamps
- Show clear task names and status
- Use dark theme if it improves contrast
- Annotate key areas (arrows, highlights) if needed

### ❌ DON'T:
- Crop out important information
- Use low resolution (blurry text)
- Hide sensitive data (passwords, API keys) - use dummy values
- Capture while page is loading
- Include unrelated browser tabs

---

## Tools for Screenshots

### Windows:
- **Snipping Tool**: Win + Shift + S
- **Snip & Sketch**: Built-in, save as PNG
- **ShareX**: Advanced (https://getsharex.com/)

### Annotation Tools:
- **Greenshot**: Free, includes editor
- **LightShot**: Quick annotations
- **Snagit**: Professional (paid)

---

## Organizing Screenshots

Create folder structure:

```
screenshots/
  airflow/
    01_dag_list_view.png
    02_dag_graph_view.png
    03_dag_tree_view.png
    04_task_instance_details.png
    05_task_logs.png
    06_success_run.png
  dashboard/
    streamlit_overview.png
    sales_chart.png
    quality_metrics.png
  database/
    schema_diagram.png
    audit_table.png
  tests/
    pytest_results.png
    coverage_report.png
```

---

## Video Walkthrough (Optional)

For extra credit, record a 2-3 minute screen recording:

**Tools**:
- **OBS Studio** (free): https://obsproject.com/
- **Loom** (free tier): https://loom.com/
- **Windows Game Bar**: Win + G

**Script**:
1. Show DAG list
2. Trigger manual run
3. Navigate to Graph view
4. Show task progression (refresh to see status updates)
5. Open task logs
6. Show final success state
7. Query database to show loaded data

**Export**: MP4, 1080p, < 50MB

---

## Submission Format

Create a ZIP file or PDF document:

### Option 1: ZIP Archive
```
ETL_Project_Screenshots.zip
  /airflow/
  /dashboard/
  /database/
  /tests/
  README.txt (explaining each screenshot)
```

### Option 2: PDF Document
1. Create Word/Google Doc
2. Insert screenshots with captions
3. Add descriptions under each
4. Export as PDF: `ETL_Project_Screenshots.pdf`

---

## Common Issues

### Screenshot is Blank/Black
- Disable hardware acceleration in browser
- Use browser's built-in screenshot (F12 → Ctrl+Shift+P → "Screenshot")

### Airflow UI Not Loading
- Verify webserver is running: `airflow webserver --port 8080`
- Check logs: `tail -f $AIRFLOW_HOME/logs/scheduler/latest/*.log`

### Tasks Not Appearing Green
- Wait for all tasks to complete (can take 1-5 minutes)
- Refresh browser page
- Check task logs for errors

---

## Verification Script

Run before capturing screenshots to ensure setup is correct:

```powershell
# Verify Airflow is running
$response = Invoke-WebRequest -Uri "http://localhost:8080/health" -UseBasicParsing
if ($response.StatusCode -eq 200) {
    Write-Host "✅ Airflow webserver is running"
} else {
    Write-Host "❌ Airflow webserver not accessible"
}

# Verify database connection
python -c "
from sqlalchemy import create_engine
import os
engine = create_engine(os.getenv('DATABASE_URL'))
conn = engine.connect()
result = conn.execute('SELECT COUNT(*) FROM ingest_audit').scalar()
print(f'✅ Database connected, {result} audit records found')
conn.close()
"

# Verify DAG exists
airflow dags list | findstr etl_pipeline
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ etl_pipeline DAG found"
} else {
    Write-Host "❌ etl_pipeline DAG not found"
}
```

---

**Ready to capture screenshots?** Follow the numbered steps above and check off each screenshot in the checklist!

**Questions?** See troubleshooting section or review Airflow documentation.

---

**Last Updated**: November 2025  
**Maintainer**: Data Engineering Team
