# Dockerfile for e(BE:L)
FROM ubuntu:20.10
LABEL maintainer="Christian.Ebeling@gmail.com"

RUN apt-get update; DEBIAN_FRONTEND="noninteractive" apt-get install -y --no-install-recommends \
    git python3 python3-pip mysql-client; \
    rm -rf /var/lib/apt/lists/*;

# flask server
EXPOSE 5000
WORKDIR /root/app

COPY requirements.txt .
RUN pip3 install -r requirements.txt
RUN git clone https://github.com/orientechnologies/pyorient.git
RUN pip3 install ./pyorient
RUN rm -rf ./pyorient && mkdir -p /root/.ebel
COPY ./docs/files/example_config.ini /root/.ebel/config.ini

# Install e(BE:L)
VOLUME ["/root/.ebel"]
COPY . .
RUN pip3 install .
WORKDIR /root/bel_projects
CMD ebel serve
