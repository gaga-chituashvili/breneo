import joblib, os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

model = joblib.load(os.path.join(BASE_DIR, 'ml/ml_model.pkl'))
le_domain = joblib.load(os.path.join(BASE_DIR, 'ml/le_domain.pkl'))
le_difficulty = joblib.load(os.path.join(BASE_DIR, 'ml/le_difficulty.pkl'))

def predict_answer(domain, difficulty):
    d = le_domain.transform([domain])[0]
    diff = le_difficulty.transform([difficulty])[0]
    return model.predict([[d, diff]])[0]