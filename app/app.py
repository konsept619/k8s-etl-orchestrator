import os

for key, value in os.environ.items():
    print(f"{key}: {value}")

while True:
    time.sleep(60)
