print("Start")
try:
    from app import app
    print("App imported")
except Exception as e:
    print(f"Error: {e}")
