FROM python:3
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /opt/docs
COPY requirements.txt /opt/docs
RUN pip install -r requirements.txt
COPY . /opt/docs
EXPOSE 8001
