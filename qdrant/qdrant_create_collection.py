
from qdrant_client import qdrant_client, models
from .provider import db_handler

def creat_collection(host,port,name):
    client = qdrant_client.QdrantClient(host = host, port= port)
    vectors_config = {"image_vector": models.VectorParams(size=640, distance=models.Distance.COSINE),
    
    }
    client.create_collection(collection_name=name,
                            vectors_config=vectors_config)
    print("coll create")


# def create_cloud_collection(host,port,name,test = False):
#     remote_client = qdrant_client.QdrantClient(
#         url="https://1e4f0ece-ef90-4a36-ae4f-2735137fbaf6.us-east-1-0.aws.cloud.qdrant.io:6333", 
#         api_key="r6uriiH8KiALX1Ze5WLNHYLTgdAAa7TZ-xt5Zw2MBQ_Uj0_JUqIR8Q",
#     )
#     vectors_config = {"image_vector": models.VectorParams(size=640, distance=models.Distance.COSINE)
#     }
#     remote_client.recreate_collection(collection_name=name,vectors_config=vectors_config)

#     if test == True:
#         local_client = qdrant_client.QdrantClient(host = host, port= port)

#         res = db_handler.retrieve_by_id(1,True,True)
#         remote_client.upload_records(name,res)

        