import requests

url = "https://olefinic-claude-interchangeably.ngrok-free.dev/predict"

text = input("Enter text to process: ")

response = requests.post(url, json={"text": text})

print("Status code:", response.status_code)
print("Response text:", response.text)


result = response.json()
print("Detected emotion:", result["emotion"])
print("Score:", result["score"])

