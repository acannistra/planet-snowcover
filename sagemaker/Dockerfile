## Thid dockerfile must be built with planet-snowcover repository context.

FROM ubuntu:18.04

MAINTAINER Tony Cannistra <tony.cannistra@gmail.com>

RUN apt-get update \
    && apt-get install -y software-properties-common curl \
    && apt autoremove -y \
    && apt-get update \
    && apt-get install -y build-essential

RUN apt-get -y update && apt-get install -y --no-install-recommends \
         wget \
         nginx \
         bzip2 \
		     libgcc-5-dev \
         ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get -y update && apt-get install -y python3-pip
RUN pip3 install setuptools


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

ENV PYTHONUNBUFFERED=TRUE
ENV PYTHONDONTWRITEBYTECODE=TRUE

RUN apt-get install -y git 

SHELL ["/bin/bash", "-c"]  
RUN echo "source activate pytorch_p36" > ~/.bashrc
ENV PATH="/opt/conda/envs/pytorch_p36/bin:${PATH}"
ENV PATH="/opt/program:${PATH}"

# Set up the program in the image
COPY start.sh /opt/program
WORKDIR /opt/program
ENTRYPOINT ["/bin/bash", "start.sh"]
