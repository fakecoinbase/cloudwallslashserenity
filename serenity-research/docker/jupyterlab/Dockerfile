FROM jupyter/datascience-notebook
USER root

RUN apt update && apt install --yes git

USER $NB_USER

COPY $PWD/requirements.txt /app/requirements.txt

RUN pip install -r /app/requirements.txt && \
    jupyter labextension install @jupyterlab/git --no-build && \
    jupyter labextension install nbdime-jupyterlab --no-build && \
    jupyter labextension install beakerx-jupyterlab --no-build && \
    jupyter serverextension enable --py jupyterlab_git && \
    jupyter lab build

WORKDIR /home/jovyan/work

RUN git clone https://github.com/cloudwall/serenity.git

CMD ["start.sh", "jupyter", "lab", "--notebook-dir=/home/jovyan/work/serenity"]