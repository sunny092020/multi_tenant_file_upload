FROM python:3 AS builder
ENV PYTHONUNBUFFERED=1

# create directory for the app user
ENV HOME=/home/app
ENV APP_HOME=$HOME/web

RUN mkdir -p $HOME \
    mkdir $APP_HOME \
    mkdir $APP_HOME/staticfiles \
    mkdir $APP_HOME/mediafiles

WORKDIR $APP_HOME

COPY ./requirements.txt $APP_HOME
RUN pip install -r requirements.txt

FROM python:3-slim

EXPOSE 8000

# create directory for the app user
ENV HOME=/home/app
ENV APP_HOME=$HOME/web

COPY --from=builder $HOME $HOME
COPY --from=builder /usr/local/ /usr/local/

RUN ldconfig /usr/local/lib
WORKDIR $APP_HOME

COPY . $APP_HOME
