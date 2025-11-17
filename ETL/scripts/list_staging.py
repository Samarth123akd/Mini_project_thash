import os
root = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'staging')
print('STAGING_PATH:', root)
print('EXISTS:', os.path.exists(root))
if not os.path.exists(root):
    print('NO_DIR')
else:
    any_files = False
    for dirpath, dirnames, filenames in os.walk(root):
        for f in filenames:
            any_files = True
            print(os.path.join(dirpath, f))
    if not any_files:
        print('NO_FILES')
