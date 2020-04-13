FROM python:3.7-slim-buster
MAINTAINER Kyle F. Downey "kyle.downey@gmail.com"

# copy the config file
USER root
RUN mkdir -p /etc/jupyter
COPY $PWD/jupyter_notebook_config.py /etc/jupyter/jupyter_notebook_config.py

# install dependencies for Git extension and JupyterLab build
RUN apt update && apt install --yes git nodejs npm

# install MiniConda so we can build our own BeakerX
ENV CONDA_DIR=/opt/conda \
    MINICONDA_VERSION=4.8.2 \
    MINICONDA_MD5=87e77f097f6ebb5127c77662dfc3165e \
    CONDA_VERSION=4.8.2

RUN cd /tmp && \
    wget --quiet https://repo.continuum.io/miniconda/Miniconda3-py37_${MINICONDA_VERSION}-Linux-x86_64.sh && \
    echo "${MINICONDA_MD5} *Miniconda3-py37_${MINICONDA_VERSION}-Linux-x86_64.sh" | md5sum -c - && \
    /bin/bash Miniconda3-py37_${MINICONDA_VERSION}-Linux-x86_64.sh -f -b -p $CONDA_DIR && \
    rm Miniconda3-py37_${MINICONDA_VERSION}-Linux-x86_64.sh && \
    echo "conda ${CONDA_VERSION}" >> $CONDA_DIR/conda-meta/pinned && \
    conda config --system --prepend channels conda-forge && \
    conda config --system --set auto_update_conda false && \
    conda config --system --set show_channel_urls true && \
    conda config --system --set channel_priority strict && \
    if [ ! $PYTHON_VERSION = 'default' ]; then conda install --yes python=$PYTHON_VERSION; fi && \
    conda list python | grep '^python ' | tr -s ' ' | cut -d '.' -f 1,2 | sed 's/$/.*/' >> $CONDA_DIR/conda-meta/pinned && \
    conda install --quiet --yes conda && \
    conda install --quiet --yes pip && \
    conda update --all --quiet --yes && \
    conda clean --all -f -y

# install stock requirements and labextensions
COPY $PWD/requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt && \
    jupyter labextension install @jupyterlab/git --no-build && \
    jupyter labextension install @jupyter-widgets/jupyterlab-manager && \
    jupyter labextension install @jupyterlab/plotly-extension --no-build && \
    jupyter labextension install beakerx-jupyterlab && \
    jupyter labextension install nbdime-jupyterlab --no-build && \
    jupyter serverextension enable --py jupyterlab_git && \
    jupyter lab build

# workaround for Pandas incompatibility until beakerx 1.5.0 released
WORKDIR /app
RUN git clone https://github.com/twosigma/beakerx.git

WORKDIR /app/beakerx
RUN conda env create -n labx -f configuration.yml
RUN conda activate labx
RUN conda install -y -c conda-forge jupyterlab
RUN pip install -r requirements.txt --verbose
RUN beakerx install
RUN jupyter labextension install @jupyter-widgets/jupyterlab-manager

WORKDIR /app/beakerx/js/lab
RUN jupyter labextension install . --no-build
WORKDIR /app/beakerx/js/lab-theme-dark
RUN jupyter labextension install . --no-build
WORKDIR /app/beakerx/js/lab-theme-light
RUN jupyter labextension install . --no-build
RUN jupyter lab build

# set up a serenity user so we are not running under root
RUN groupadd -r serenity && useradd -s /bin/bash --create-home --no-log-init -r -g serenity serenity

USER serenity
RUN mkdir -p /home/serenity/dev/shadows
WORKDIR /home/serenity/dev/shadows

CMD ["jupyter", "lab"]
