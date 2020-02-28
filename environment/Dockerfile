FROM ubuntu:16.04

MAINTAINER Tony Cannistra <tony.cannistra@gmail.com>

RUN apt-get update > /dev/null 2>&1 \
    && apt-get install -y software-properties-common curl > /dev/null 2>&1 \
    && apt autoremove -y > /dev/null 2>&1 \
    && apt-get update  > /dev/null 2>&1\
    && apt-get install -y build-essential > /dev/null 2>&1


RUN apt-get -y update > /dev/null 2>&1 && apt-get install -y --no-install-recommends \
         wget \
         nginx \
         bzip2 \
		     libgcc-5-dev \
         ca-certificates > /dev/null 2>&1\
    && rm -rf /var/lib/apt/lists/*

RUN apt-get install -y software-properties-common > /dev/null 2>&1 \
    && add-apt-repository ppa:deadsnakes/ppa > /dev/null 2>&1 \
    && apt-get -y update > /dev/null 2>&1 \
    && apt-get install -y python3.6 > /dev/null 2>&1

RUN wget https://bootstrap.pypa.io/get-pip.py > /dev/null 2>&1 && python3.6 get-pip.py
RUN pip install setuptools > /dev/null 2>&1


# Anaconda
RUN wget https://repo.continuum.io/archive/Anaconda3-5.0.1-Linux-x86_64.sh > /dev/null 2>&1
RUN bash Anaconda3-5.0.1-Linux-x86_64.sh -b > /dev/null 2>&1
RUN rm Anaconda3-5.0.1-Linux-x86_64.sh
ENV PATH /root/anaconda3/bin:$PATH

# Install dependancies
RUN apt-get update \
    && apt-get install -y libsm6 libxext6 libxrender-dev
COPY ./environment/pytorch_p36.yml /opt/program/
RUN conda env update -q --file /opt/program/pytorch_p36.yml
COPY ./environment/credentials /root/.aws/credentials


ENV PYTHONUNBUFFERED=TRUE
ENV PYTHONDONTWRITEBYTECODE=TRUE

RUN apt-get install -y git > /dev/null 2>&1

SHELL ["/bin/bash", "-c"]
RUN echo "source activate pytorch_p36" > ~/.bashrc
ENV PATH="/opt/conda/envs/pytorch_p36/bin:${PATH}"
ENV PATH="/opt/program:${PATH}"

# Set up the program in the image
COPY ./environment/start.sh /opt/program
WORKDIR /opt/program
ENTRYPOINT ["/bin/bash", "start.sh"]
