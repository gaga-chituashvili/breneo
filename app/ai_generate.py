import os, requests, re
from .models import Question

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def generate_question(domain="Python", difficulty="Easy"):
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

    resp = requests.post(url, headers=headers, json=data)
    if resp.status_code != 200:
        print("API error:", resp.text)
        return None

    content = resp.json()["choices"][0]["message"]["content"]
    lines = [l.strip() for l in content.split("\n") if l.strip()]
    if len(lines) < 6: return None

    text = lines[0]
    options = lines[1:5]
    match = re.search(r"\d", lines[5])
    correct_option = int(match.group()) if match else 1

    q = Question.objects.create(
        text=text,
        domain=domain,
        difficulty=difficulty,
        option1=options[0],
        option2=options[1],
        option3=options[2],
        option4=options[3],
        correct_option=correct_option
    )
    return q

def generate_multiple_questions(n=5, domain="Python", difficulty="Easy"):
    questions = []
    for _ in range(n):
        q = generate_question(domain, difficulty)
        if q:
            questions.append(q)
    return questions