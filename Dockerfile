ARG TORCH_VERSION = 1.7.1
FROM pytorch/pytorch:${TORCH_VERSION}-cpu

# FROM python:3.8

RUN pip install git+https://github.com/openai/CLIP.git
# RUN python3 --version


WORKDIR /opt/irs

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

VOLUME ["/opt/irs/static"]

# LABEL org.opencontainers.image.authors="EdgeNeko" \
#       org.opencontainers.image.title="NekoImageGallery" \
#       org.opencontainers.image.description="An AI-powered natural language & reverse Image Search Engine powered by CLIP & qdrant."

ENTRYPOINT ["python", "app.py"]
# CMD [ "python", "app.py" ]