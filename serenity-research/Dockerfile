FROM python:3.8-slim-buster
USER root

RUN apt update && apt install --yes git nodejs npm

COPY $PWD/requirements.txt /app/requirements.txt

RUN pip install -r /app/requirements.txt && \
    jupyter labextension install @jupyterlab/git --no-build && \
    jupyter labextension install nbdime-jupyterlab --no-build && \
    jupyter serverextension enable --py jupyterlab_git && \
    jupyter lab build

RUN groupadd -r serenity && useradd --create-home --no-log-init -r -g serenity serenity

USER serenity
RUN mkdir -p /home/serenity/dev/shadows
WORKDIR /home/serenity/dev/shadows

RUN git clone https://github.com/cloudwall/serenity.git

CMD ["jupyter", "lab", "--ip=*", "--port=8888", "--no-browser", "--notebook-dir=/home/serenity/dev/shadows/serenity"]
