# nazala_backend
NaZaLa Backend Project

first commit

### Prerequisites
- Python 3.12

### How to run this project in your local folder
cd your_folder_of_this_project

#### if you never run this before
    python3 -m venv venv
    source venv/bin/activate
    //如果没有log 文件需要重新创建
    mkdir -p logs
    : > logs/django.log
    pip install -r requirements.txt
    python manage.py makemigrations
    python manage.py migrate
    python manage.py createsuperuser
#### else
    source venv/bin/activate
#### end if

    python manage.py runserver

Then visit http://127.0.0.1:8000



# Test
## How to run
 - python manage.py test -v 2

