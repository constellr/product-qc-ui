# Build stage
# Installing PDM and required dependencies in the first stage of the building
FROM --platform=linux/amd64 python:3.12 AS builder

# RUN apt-get update -y
# RUN apt-get -y install gdal-bin libgdal-dev
RUN pip install -U pip setuptools wheel
RUN pip install pdm

COPY pdm.lock pyproject.toml /app/

WORKDIR /app
RUN mkdir __pypackages__

RUN pdm sync --prod --no-editable

# Run stage
# Consists in starting fresh without pdm but by copy pasting the installed packages
FROM --platform=linux/amd64 python:3.12

# retrieve packages from build stage

ENV PYTHONPATH=/app/pkgs
COPY --from=builder /app/__pypackages__/3.12/lib /app/pkgs

# retrieve executables
COPY --from=builder /app/__pypackages__/3.12/bin/* /bin/

# Specific to streamlit usgae
RUN adduser -u 1000 --disabled-password --gecos "" appuser
USER appuser
COPY ./src /app
EXPOSE 8501

WORKDIR /app
ENV CONFIG_PATH=/app/config/docker.toml

# ENTRYPOINT ["streamlit", "run", "main.py", "--server.port=8501", "--global.developmentMode=false"]
