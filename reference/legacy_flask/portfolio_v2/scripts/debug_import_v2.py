print("Start")
try:
    from import_v2 import import_data
    print("Import_v2 imported")
except Exception as e:
    import traceback
    traceback.print_exc()
