FROM python:3.14-alpine
WORKDIR /code

COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir -r /code/requirements.txt


COPY ./ /code

RUN chmod +x /code/start.sh

EXPOSE 8000

CMD ["/code/start.sh"]