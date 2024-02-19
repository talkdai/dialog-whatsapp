FROM ghcr.io/talkdai/dialog:latest

# Copy the plugin code
WORKDIR /plugin
COPY . .

RUN pip install -e .

WORKDIR /app/src/

RUN mkdir /app/static