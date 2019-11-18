FROM python:3
EXPOSE 5000
ADD server.py /
ADD /templates/test.html /templates/
RUN pip3 install redis
RUN pip3 install flask
ENTRYPOINT ["python3", "server.py"]
