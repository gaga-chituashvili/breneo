import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import joblib, os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# მაგალითის მონაცემები (შეავსე რეალური მონაცემებით)
data = [
    {"user_id": 1, "domain": "Python", "difficulty": "Easy", "answer_correct": 1},
    {"user_id": 1, "domain": "Python", "difficulty": "Medium", "answer_correct": 0},
    {"user_id": 2, "domain": "Python", "difficulty": "Easy", "answer_correct": 1},
    {"user_id": 2, "domain": "Java", "difficulty": "Hard", "answer_correct": 0},
]

df = pd.DataFrame(data)

le_domain = LabelEncoder()
le_difficulty = LabelEncoder()

df['domain'] = le_domain.fit_transform(df['domain'])
df['difficulty'] = le_difficulty.fit_transform(df['difficulty'])

X = df[['domain', 'difficulty']]
y = df['answer_correct']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = RandomForestClassifier()
model.fit(X_train, y_train)

# შეიქმენი ml ფოლდერი, თუ არ არსებობს
os.makedirs(os.path.join(BASE_DIR, 'ml'), exist_ok=True)

joblib.dump(model, os.path.join(BASE_DIR, 'ml/ml_model.pkl'))
joblib.dump(le_domain, os.path.join(BASE_DIR, 'ml/le_domain.pkl'))
joblib.dump(le_difficulty, os.path.join(BASE_DIR, 'ml/le_difficulty.pkl'))

print("Model trained and saved!")
