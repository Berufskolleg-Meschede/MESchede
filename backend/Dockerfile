FROM python:3.14-alpine
WORKDIR /code

COPY ./requirements.txt /code
RUN pip install --no-cache-dir -r code/requirements.txt
EXPOSE 80

COPY . /code

CMD ["fastapi", "run", "app/main.py", "--port", "80"]