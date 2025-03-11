FROM python:3.11.0


RUN apt-get update && apt-get install -y python3-pip python3-dev
RUN apt-get install -y python3-pip
RUN apt-get install -y python3-dev
WORKDIR /app



EXPOSE 5000
COPY . .
RUN pip install -r requirements.txt
CMD [ "python3", "main.py" ]