from typing import Optional

import qdrant_client
from qdrant_client.http import models
from qdrant_client import QdrantClient
from config.config import configure as cf
from .img_data import ImageData

class VectorDbHandler:
    IMG_VECTOR = "image_vector"
    AVAILABLE_POINT_TYPES = [models.Record,models.ScoredPoint,models.PointStruct]

    def __init__(self) -> None:
        # self._client = qdrant_client.AsyncQdrantClient(host=cf.qdrant.host, port=cf.qdrant.port,
        #                                 grpc_port=cf.qdrant.grpc_port, api_key=cf.qdrant.api_key,
        #                                 prefer_grpc=cf.qdrant.prefer_grpc )
        self._client = QdrantClient(host=cf.qdrant.host, port=cf.qdrant.port,
                                        grpc_port=cf.qdrant.grpc_port, api_key=cf.qdrant.api_key,
                                        prefer_grpc=cf.qdrant.prefer_grpc )
        
        self.collection_name = cf.qdrant.coll
    def retrieve_by_id(self, img_id: int, with_payload = False, with_vector = False):
        res = self._client.retrieve(collection_name=self.collection_name,
                                        ids = [img_id],
                                        with_payload=with_payload,
                                        with_vectors= with_vector)
        print(res)
        return res[0]
    
    def query_search(self, query_vector,top_k = 50,skip=0) -> list[Search]:
        res = self._client.search(collection_name=self.collection_name,
                                query_vector=("image_vector",[]),
                                limit=10)
        print(res)


    def delItems(self, points):
        # points = list(range(15))
        res =  self._client.delete(
            collection_name=self.collection_name,
            points_selector=models.PointIdsList(
                points= points
            )
        )
        print(res.status)

    def get_counts(self,exact):
        res =  self._client.count(collection_name=self.collection_name, exact=exact) 
        return res.count

    def insertItems(self, item: ImageData):
        points = [self._get_point_from_img_data(item)]

        res =  self._client.upsert(collection_name=self.collection_name,
                                        wait=True,
                                        points=points)
        # print(res.status)
    

    @classmethod
    def _get_vector_from_img_data(cls,img_data: ImageData) -> models.PointVectors:
        vector = {}
        if img_data.image_vector is not None:
            vector["image_vector"] = img_data.image_vector.tolist()
        return models.PointVectors(
            id=str(img_data.id),
            vector=vector
        )
    
    @classmethod
    def _get_point_from_img_data(cls, img_data: ImageData) -> models.PointStruct:
        return models.PointStruct(
            id = img_data.id,
            payload=img_data.payload,
            vector = cls._get_vector_from_img_data(img_data).vector
        )
    
    