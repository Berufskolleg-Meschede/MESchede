FROM python:3.14-alpine
WORKDIR /code

COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir -r /code/requirements.txt
EXPOSE 8000

COPY ./ /code

CMD ["fastapi", "run", "app/main.py", "--port", "8000"]