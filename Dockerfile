FROM python:3.11.0


WORKDIR /app



EXPOSE 5000
COPY . .
RUN pip install -r requirements.txt
CMD [ "python3", "main.py" ]