# django_sprint4

<img src="https://raw.githubusercontent.com/AKhlebnov/django_sprint4/main/blogicum/static/img/logo.png" width="24" height="24"> Блогикум

## Описание проекта

Блогикум - это социальная сеть для создания, ведения и комментирования блогов.

### Технологии

- Python 3.9
- Django 3.2
- bootstrap5 22.2
- SQLite3

### Установка

Для запуска приложения проделайте следующие шаги:

1. Склонируйте репозиторий.

2. Перейдите в папку с кодом и создайте виртуальное окружение:
```
python -m venv venv
```

3. Активируйте виртуальное окружение:
```
source venv\scripts\activate
```
4. Установите зависимости:
```
python -m pip install -r requirements.txt
```
5. Выполните миграции:
```
python manage.py migrate
```
6. Создайте суперпользователя:
```
python manage.py createsuperuser
```
7. Запустите сервер:
```
python manage.py runserver
```
