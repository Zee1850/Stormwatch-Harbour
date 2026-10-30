import os
import json
import urllib.request
import urllib.error

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    print("ERROR: API key not found.")
    raise SystemExit

url = "https://generativelanguage.googleapis.com/v1beta/interactions"

data = {
    "model": "gemini-3.8-flash",
    "input": "Reply with exactly: Gemini connection successful!"
}

request = urllib.request.Request(
    url,
    data=json.dumps(data).encode("utf-8"),
    headers={
        "Content-Type": "application/json",
        "x-goog-api-key": API_KEY
    },
    method="POST"
)

try:
    with urllib.request.urlopen(request, timeout=60) as response:
        result = json.loads(response.read().decode("utf-8"))

    answer = result.get("output_text")

    if not answer:
        for step in result.get("steps", []):
            if step.get("type") == "model_output":
                for item in step.get("content", []):
                    if item.get("type") == "text":
                        answer = item.get("text")
                        break

    if answer:
        print("\nSUCCESS! Gemini responded:")
        print(answer)
    else:
        print("Response received, but text was not found:")
        print(json.dumps(result, indent=2))

except urllib.error.HTTPError as error:
    print("\nAPI ERROR:", error.code)
    print(error.read().decode("utf-8"))

except Exception as error:
    print("\nCONNECTION ERROR:", error)