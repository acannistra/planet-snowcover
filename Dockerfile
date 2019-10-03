FROM ubuntu:16.04

MAINTAINER Tony Cannistra <tony.cannistra@gmail.com>

RUN apt-get update \
    && apt-get install -y software-properties-common curl \
    && add-apt-repository ppa:jonathonf/python-3.6 \
    && apt autoremove -y \
    && apt-get update \
    && apt-get install -y build-essential \
    && apt-get install -y python3.6

RUN apt-get -y update && apt-get install -y --no-install-recommends \
         wget \
         nginx \
         bzip2 \
		     libgcc-5-dev \
         ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN wget https://bootstrap.pypa.io/get-pip.py && python3.6 get-pip.py
RUN pip install setuptools
RUN pip install --no-cache-dir notebook==5.*



# Anaconda
RUN wget https://repo.continuum.io/archive/Anaconda3-5.0.1-Linux-x86_64.sh
RUN bash Anaconda3-5.0.1-Linux-x86_64.sh -b
RUN rm Anaconda3-5.0.1-Linux-x86_64.sh
ENV PATH /root/anaconda3/bin:$PATH

# Install dependancies
COPY pytorch_p36.yml /opt/program/
RUN conda env update --file /opt/program/pytorch_p36.yml
RUN apt-get update \
    && apt-get install -y libsm6 libxext6 libxrender-dev
COPY credentials /root/.aws/credentials

# There's substantial overlap between scipy and numpy that we eliminate by
# linking them together. Likewise, pip leaves the install caches populated which uses
# a significant amount of space. These optimizations save a fair amount of space in the
# image, which reduces start up time.

# Set some environment variables. PYTHONUNBUFFERED keeps Python from buffering our standard
# output stream, which means that logs can be delivered to the user quickly. PYTHONDONTWRITEBYTECODE
# keeps Python from writing the .pyc files which are unnecessary in this case. We also update
# PATH so that the train and serve programs are found when the container is invoked.

ENV PYTHONUNBUFFERED=TRUE
ENV PYTHONDONTWRITEBYTECODE=TRUE

SHELL ["/bin/bash", "-c"]
RUN echo "source activate pytorch_p36" > ~/.bashrc
ENV PATH="/opt/conda/envs/pytorch_p36/bin:${PATH}"
ENV PATH="/opt/program:${PATH}"

ARG NB_USER=jovyan
ARG NB_UID=1000
ENV USER ${NB_USER}
ENV NB_UID ${NB_UID}
ENV HOME /home/${NB_USER}

RUN adduser --disabled-password \
    --gecos "Default user" \
    --uid ${NB_UID} \
    ${NB_USER}

COPY . ${HOME}
USER root
RUN chown -R ${NB_UID} ${HOME}
USER ${NB_USER}
