FROM python:3
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /opt/auth
COPY requirements.txt /opt/auth
RUN pip install -r requirements.txt
COPY . /opt/auth
EXPOSE 8000
