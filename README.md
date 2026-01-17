## 🧠 Project Overview

BRENE01 is a Django REST API project that provides user management, media uploads,
and machine learning–based predictions using a pre-trained model.
The backend is designed to be scalable and easily integrated with frontend
applications such as React.


## 📁 Project Structure

BRENE01/
│
├── .venv/                     # Python virtual environment
├── app/                       # Main Django app
│   ├── __pycache__/           # Python cache files
│   ├── management/            # Custom Django management commands
│   ├── migrations/            # Database migration files
│   ├── ml/                    # Machine Learning models and scripts
│   │   └── model.pkl          # Serialized ML model
│   ├── __init__.py            # Marks this directory as a Python package
│   ├── admin.py               # Django admin configurations
│   ├── apps.py                # App configuration
│   ├── models.py              # Database models
│   ├── serializers.py         # DRF serializers
│   ├── tests.py               # Unit tests
│   ├── urls.py                # App-level URL routing
│   └── views.py               # API / view logic
│
├── media/                     # Uploaded media files
│   └── profile_pics/          # User profile pictures
│
├── mysite/                    # Django project settings
│   ├── __pycache__/           # Python cache files
│   ├── __init__.py            # Marks this directory as a Python package
│   ├── asgi.py                # ASGI config for async servers
│   ├── settings.py            # Django settings
│   ├── urls.py                # Project-level URL routing
│   └── wsgi.py                # WSGI config for deployment
│
├── profile_pics/              # Possibly another directory for profile pictures
├── staticfiles/               # Collected static files
│   ├── admin/                 # Django admin static files
│   └── rest_framework/        # DRF static files
│
├── .env                       # Environment variables
├── .gitignore                 # Git ignore rules
├── db.sqlite3                 # SQLite database
├── manage.py                  # Django management script
├── Procfile                   # Deployment config (Heroku etc.)
└── requirements.txt           # Python dependencies




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
