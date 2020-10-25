FROM ubuntu:16.04
ENV LC_ALL=en_US.UTF-8

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
         ca-certificates libspatialindex-dev \
         libsm6 libxext6 libxrender-dev cmake \
    && rm -rf /var/lib/apt/lists/*

# Anaconda
RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
RUN bash Miniconda3-latest-Linux-x86_64.sh -b
ENV PATH /root/miniconda3/bin:$PATH


# Install dependancies
COPY process_results.yml /opt/program/
RUN conda env update --file /opt/program/process_results.yml

RUN pip install --upgrade awscli
