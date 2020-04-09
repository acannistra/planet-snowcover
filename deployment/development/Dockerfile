FROM jupyter/datascience-notebook:9f9e5ca8fe5a

COPY ./deployment/environment/pytorch_p36.yml /tmp/
RUN conda env update -q --yes --file /opt/program/pytorch_p36.yml \
  fix-permissions $CONDA_DIR && \
  fix-permissions /home/$NB_USER
