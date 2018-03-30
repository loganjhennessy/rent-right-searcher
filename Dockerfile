FROM ubuntu:17.10

ADD . /opt/searcher

# Apt-get stuff
RUN apt-get update
RUN apt-get -y install python3-pip

# Pip stuff
RUN pip3 install --upgrade pip
RUN pip3 install -r /opt/searcher/requirements.txt

ENTRYPOINT ["python3","/opt/searcher/run.py"]
