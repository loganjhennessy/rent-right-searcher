FROM ubuntu:17.10

ADD . /opt/rent-right-searcher

# Apt-get stuff
RUN apt-get update
RUN apt-get -y install python3-pip

# Pip stuff
RUN pip3 install --upgrade pip
RUN pip3 install -r /opt/rent-right-searcher/requirements.txt
RUN pip3 install -e /opt/rent-right-searcher

ENTRYPOINT ["python3","/opt/rent-right-searcher/rentrightsearcher/main.py"]
