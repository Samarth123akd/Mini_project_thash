"""Simple test harness to run test_ functions in test modules under tests/.
This avoids requiring pytest in the environment.
"""
import importlib.util
import inspect
import os
import sys
import tempfile
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

TEST_DIR = os.path.join(ROOT, 'tests')

results = []
for fname in sorted(os.listdir(TEST_DIR)):
    if not fname.startswith('test_') or not fname.endswith('.py'):
        continue
    path = os.path.join(TEST_DIR, fname)
    mod_name = os.path.splitext(fname)[0]
    spec = importlib.util.spec_from_file_location(mod_name, path)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception as e:
        results.append((mod_name, '<module import>', False, e))
        continue

    for name, func in inspect.getmembers(mod, inspect.isfunction):
        if not name.startswith('test_'):
            continue

        # Prepare simple fixtures: currently only support `tmp_path` (pytests tmp_path)
        sig = inspect.signature(func)
        kwargs = {}
        if 'tmp_path' in sig.parameters:
            td = tempfile.TemporaryDirectory()
            # keep the tempdir object alive until after function runs
            tmp_path = Path(td.name)
            kwargs['tmp_path'] = tmp_path

        try:
            func(**kwargs)
            results.append((mod_name, name, True, None))
        except Exception as e:
            results.append((mod_name, name, False, e))
        finally:
            # clean up tempdir if created
            if 'tmp_path' in kwargs:
                td.cleanup()

# Print summary
failed = [r for r in results if not r[2]]
for mod, name, ok, exc in results:
    status = 'PASS' if ok else 'FAIL'
    print(f"{mod}.{name}: {status}")
    if exc is not None:
        print('  ', repr(exc))

print('\nSummary:')
print(f'  Total tests: {len(results)}')
print(f'  Passed: {len(results) - len(failed)}')
print(f'  Failed: {len(failed)}')

if failed:
    sys.exit(2)
else:
    sys.exit(0)
