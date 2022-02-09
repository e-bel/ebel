# Dockerfile for e(BE:L)
FROM python:3.9-slim
LABEL maintainer="Christian.Ebeling@gmail.com"

RUN apt-get update \
    && apt-get install -y --no-install-recommends git nano \
    && pip install --upgrade pip \
    && rm -rf /var/lib/apt/lists/*;

WORKDIR /root/app
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN git clone https://github.com/orientechnologies/pyorient.git
RUN pip install ./pyorient
RUN rm -rf ./pyorient && mkdir -p /root/.ebel
# COPY ./docs/files/example_config.ini /root/.ebel/config.ini

# Install e(BE:L)
VOLUME ["/root/.ebel"]
COPY . .
RUN pip install .
WORKDIR /root/bel_projects

# flask server
EXPOSE 5000

CMD ["ebel", "serve"]
