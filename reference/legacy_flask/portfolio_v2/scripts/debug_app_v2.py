print("Start")
try:
    from app_v2 import app
    print("App V2 imported")
except Exception as e:
    import traceback
    traceback.print_exc()
