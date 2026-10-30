
import os
import json
import urllib.request
import urllib.error

API_KEY = os.getenv("GROQ_API_KEY")

if not API_KEY:
    print("ERROR: API key not found.")
    raise SystemExit

url = "https://api.groq.com/openai/v1/chat/completions"

data = {
    "model": "openai/gpt-oss-20b",
    "messages": [
        {
            "role": "user",
            "content": (
                "Return exactly this JSON object: "
                '{"status": "success", "message": "Groq is working"}'
            )
        }
    ],
    "temperature": 0,
    "max_completion_tokens": 1024,
    "reasoning_effort": "low",
    "reasoning_format": "hidden",
    "response_format": {
        "type": "json_object"
    }
}

request = urllib.request.Request(
    url,
    data=json.dumps(data).encode("utf-8"),
    headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
        "User-Agent": "StormwatchHarbour/1.0"
    },
    method="POST"
)

try:
    with urllib.request.urlopen(request, timeout=60) as response:
        result = json.loads(response.read().decode("utf-8"))

    answer = result["choices"][0]["message"]["content"]

    if not answer:
        print("ERROR: Groq returned an empty response.")
        print(json.dumps(result, indent=2))
    else:
        print("\nSUCCESS! Groq responded:")
        print(answer)

except urllib.error.HTTPError as error:
    print("\nAPI ERROR:", error.code)
    print(error.read().decode("utf-8"))

except Exception as error:
    print("\nCONNECTION ERROR:", error)
