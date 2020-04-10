FROM jupyter/datascience-notebook:9f9e5ca8fe5a

COPY ./deployment/environment/pytorch_p36.yml /tmp/
RUN conda env update -q --file /tmp/pytorch_p36.yml && \
  fix-permissions $CONDA_DIR && \
  fix-permissions /home/$NB_USER

SHELL ["/bin/bash", "-c"]
RUN echo "source activate pytorch_p36" > ~/.bashrc
ENV PATH /opt/conda/envs/pytorch_p36/bin:$PATH

