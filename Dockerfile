ARG TORCH_VERSION=2.1.2
ARG CUDA_VERSION=12.1
FROM pytorch/pytorch:${TORCH_VERSION}-cuda${CUDA_VERSION}-cudnn8-runtime
# FROM python:3.8

# RUN python3 --version


WORKDIR /CLIP4CirDemo

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

VOLUME [".:/opt/IRS"]

# LABEL org.opencontainers.image.authors="EdgeNeko" \
#       org.opencontainers.image.title="NekoImageGallery" \
#       org.opencontainers.image.description="An AI-powered natural language & reverse Image Search Engine powered by CLIP & qdrant."

ENTRYPOINT ["python", "app.py"]
# CMD [ "python", "app.py" ]