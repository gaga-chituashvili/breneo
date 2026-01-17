## 🧠 Project Overview

BRENE01 is a Django REST API project that provides user management, media uploads,
and machine learning–based predictions using a pre-trained model.
The backend is designed to be scalable and easily integrated with frontend
applications such as React.


## 📁 Project Structure

BRENE01/
│
├── .venv/
├── app/
│   ├── __pycache__/
│   ├── management/
│   ├── migrations/
│   ├── ml/
│   │   └── model.pkl
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── serializers.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
│
├── media/
│   └── profile_pics/
│
├── mysite/
│   ├── __pycache__/
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── profile_pics/
├── staticfiles/
│   ├── admin/
│   └── rest_framework/
│
├── .env
├── .gitignore
├── db.sqlite3
├── manage.py
├── Procfile
└── requirements.txt



## 📦 Dependencies

This project relies on the following key libraries and tools:

- Django & Django REST Framework for backend API development
- Authentication using dj-rest-auth, django-allauth, and JWT
- Machine Learning with scikit-learn, NumPy, Pandas
- Media handling with Cloudinary and Pillow
- Email services powered by SendGrid
- Database support with SQLite (development) and PostgreSQL (production)
- Deployment using Gunicorn and WhiteNoise
- Environment variable management with python-dotenv and python-decouple

For the full list of dependencies, see `requirements.txt`.


## ⚙️ Installation & Setup

```bash
git clone https://github.com/gaga-chituashvili/breneo.git

python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
