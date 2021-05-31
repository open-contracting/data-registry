FROM python:3

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir /data
RUN mkdir /data/logs

RUN apt-get update
RUN apt-get -y install curl gnupg
RUN curl -sL https://deb.nodesource.com/setup_16.x | bash -
RUN apt-get update
RUN apt-get -y install nodejs

RUN cd /usr/src/app/data_registry/vue && rm -Rf node_modules
RUN cd /usr/src/app/data_registry/vue && npm install
RUN cd /usr/src/app/data_registry/vue && npm run build

ENTRYPOINT [ "" ]