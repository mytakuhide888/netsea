FROM python:3.9

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /code

COPY requirements.txt /code/
RUN pip install -r requirements.txt
RUN apt-get update && apt-get install -y default-mysql-client logrotate

RUN adduser --disabled-password --gecos "" niiya
#RUN echo "niiya ALL=(ALL) NOPASSWD: /usr/sbin/logrotate" >> /etc/sudoers.d/niiya
RUN mkdir -p /code/static && chown -R niiya:niiya /code/static
RUN mkdir -p /code/logs && chown -R niiya:niiya /code/logs

COPY entrypoint.sh /code/
RUN chmod +x /code/entrypoint.sh

#USER niiya

COPY . /code/
USER niiya

