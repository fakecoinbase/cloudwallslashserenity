FROM python:3.8-slim-buster
MAINTAINER Kyle F. Downey "kyle.downey@gmail.com"

# copy the config file
USER root
RUN mkdir -p /etc/jupyter
COPY $PWD/jupyter_notebook_config.py /etc/jupyter/jupyter_notebook_config.py

# install dependencies for Git extension and JupyterLab build
RUN apt update && apt install --yes git nodejs npm

COPY $PWD/requirements.txt /app/requirements.txt

RUN pip install -r /app/requirements.txt && \
    jupyter labextension install @jupyterlab/git --no-build && \
    jupyter labextension install @jupyter-widgets/jupyterlab-manager && \
    jupyter labextension install @jupyterlab/plotly-extension --no-build && \
    jupyter labextension install beakerx-jupyterlab && \
    jupyter labextension install nbdime-jupyterlab --no-build && \
    jupyter serverextension enable --py jupyterlab_git && \
    jupyter lab build

RUN groupadd -r serenity && useradd --create-home --no-log-init -r -g serenity serenity

USER serenity
RUN mkdir -p /home/serenity/dev/shadows
WORKDIR /home/serenity/dev/shadows

CMD ["jupyter", "lab"]