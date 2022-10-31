FROM python:3.9

RUN apt-get update
RUN apt-get -y install nginx sudo

RUN adduser --disabled-password --gecos '' docker
RUN adduser docker sudo

RUN echo "%docker ALL=NOPASSWD:/usr/sbin/service nginx reload" >> /etc/sudoers
RUN echo "%docker ALL=NOPASSWD:/usr/sbin/service nginx start" >> /etc/sudoers
RUN echo "%docker ALL=NOPASSWD:/bin/cp /websensor/nginx/nginx.conf /etc/nginx/sites-enabled/default" >> /etc/sudoers

# git clone the sensor code
RUN git clone https://github.com/zerodarkio/websensor.git

RUN chown -R docker /websensor

WORKDIR websensor

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install python dependencies
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# the start up script
RUN chmod +x run.sh

CMD ["sh", "-c", "/websensor/run.sh"]
