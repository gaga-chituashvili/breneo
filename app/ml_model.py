import joblib
import pandas as pd

# load model & label encoders
model = joblib.load("ml_model.pkl")
le_domain = joblib.load("le_domain.pkl")
le_difficulty = joblib.load("le_difficulty.pkl")

def predict_answer(domain, difficulty):
    domain_encoded = le_domain.transform([domain])[0]
    difficulty_encoded = le_difficulty.transform([difficulty])[0]

    df = pd.DataFrame([[domain_encoded, difficulty_encoded]], columns=['domain', 'difficulty'])
    prediction = model.predict(df)[0]
    return prediction