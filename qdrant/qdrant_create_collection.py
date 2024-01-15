import argparse

from qdrant_client import qdrant_client, models


def creat_collection(host,port,name):
    client = qdrant_client.QdrantClient(host = host, port= port)
    vectors_config = {"image_vector": models.VectorParams(size=640, distance=models.Distance.COSINE),
    
    }
    client.create_collection(collection_name=name,
                            vectors_config=vectors_config)
    print("coll create")