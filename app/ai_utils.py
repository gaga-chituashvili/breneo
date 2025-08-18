import os
import requests
import re

GROQ_API_KEY = os.getenv("GROQ_API_KEY")  # Make sure this is set in your environment

def generate_ai_question(domain="Python", difficulty="Easy"):
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {GROQ_API_KEY}"
        }
        data = {
            "model": "meta-llama/llama-4-scout-17b-16e-instruct",
            "messages": [
                {
                    "role": "user",
                    "content": (
                        f"Generate a {difficulty} multiple choice question about {domain}. "
                        "Return in format: Question text\\nOption1\\nOption2\\nOption3\\nOption4\\nCorrect option number (1-4)"
                    )
                }
            ],
            "max_tokens": 300
        }

        resp = requests.post(url, headers=headers, json=data, timeout=30)
        resp.raise_for_status()

        content = resp.json()["choices"][0]["message"]["content"]
        lines = [l.strip() for l in content.split("\n") if l.strip()]
        if len(lines) < 6:
            return None

        correct_option = re.search(r"\d", lines[5])
        if not correct_option:
            return None

        return {
            "text": lines[0],
            "option1": lines[1],
            "option2": lines[2],
            "option3": lines[3],
            "option4": lines[4],
            "correct_option": int(correct_option.group())
        }

    except Exception as e:
        print(f"Error generating AI question: {e}")
        return None
