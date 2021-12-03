FROM jupyter/datascience-notebook

USER root 

RUN apt-get -q update && \
    apt-get -q -y install gdal-bin proj-bin && \
    apt-get clean && \ 
    rm -rf /var/lib/apt/ /var/cache/apt/ /var/cache/debconf/

USER $NB_USER

COPY ./deployment/environment/pytorch_p36.yml /tmp/
RUN conda env update -q --file /tmp/pytorch_p36.yml && \
  fix-permissions $CONDA_DIR && \
  fix-permissions /home/$NB_USER

SHELL ["/bin/bash", "-c"]
RUN echo "source activate pytorch_p36" > ~/.bashrc
ENV PATH /opt/conda/envs/pytorch_p36/bin:$PATH

