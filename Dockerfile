# ARG TORCH_VERSION=1.7.1
# FROM pytorch/pytorch:${TORCH_VERSION}

FROM python:3.8-slim-buster

# RUN python3 --version


WORKDIR /opt/irs

COPY requirements.txt .

RUN apt-get update && apt-get install -y git

RUN pip install --no-cache-dir -r requirements.txt

RUN pip install git+https://github.com/openai/CLIP.git


COPY . .

EXPOSE 8000

VOLUME ["/opt/irs/static"]

# LABEL org.opencontainers.image.authors="EdgeNeko" \
#       org.opencontainers.image.title="NekoImageGallery" \
#       org.opencontainers.image.description="An AI-powered natural language & reverse Image Search Engine powered by CLIP & qdrant."


CMD [ "python", "-m" , "flask", "run", "--host=0.0.0.0"]
# ENTRYPOINT ["python", "app.py"]
# CMD [ "python", "app.py" ]