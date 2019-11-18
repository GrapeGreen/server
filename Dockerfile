FROM python:3
EXPOSE 27017
EXPOSE 5000
ADD logging.conf /
ADD server.py /
ADD /templates/test.html /templates/
RUN pip3 install redis
RUN pip3 install flask
RUN pip3 install pymongo
ENTRYPOINT ["python3", "server.py"]
