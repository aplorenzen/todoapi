FROM python:3-alpine
EXPOSE 5000
WORKDIR /usr/src/app
RUN pip install pymongo flask flask-restful flask-cors
COPY app.py /usr/src/app/app.py
CMD ["python", "-u", "app.py"]