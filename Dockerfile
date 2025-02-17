FROM python:3.11.0


WORKDIR /app



COPY . .
RUN pip install -r requirements.txt
CMD [ "python3", "main.py" ]