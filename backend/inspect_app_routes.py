import os

search_dir = os.path.join(os.path.dirname(__file__), "app")

print("=== ALL PYTHON FILES IN APP ===")
for root, dirs, files in os.walk(search_dir):
    if "__pycache__" in root:
        continue
    for file in files:
        if file.endswith(".py"):
            print(os.path.join(root, file))
