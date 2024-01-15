import argparse
import asyncio
from config.config import configure as cf
from extract_features import qdrant_index
from qdrant.qdrant_create_collection import creat_collection
from qdrant.provider import db_handler
def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument('--init-qdrant',dest='init_qdrant',action='store_true',help="Initiate Qdrant db")

    parser.add_argument('--qdrant-index',dest= "qdrant_index", action='store_true', help="store feature in qdrant")
    parser.add_argument('--delete-index',dest='delete_index',action='store_true')
    parser.add_argument('--retrieve-id',dest='retrieve_id',type=int)

    return parser.parse_args()
if __name__ == '__main__':
    

    args = parse_args()
    if args.init_qdrant:
        creat_collection(cf.qdrant.host, cf.qdrant.port, cf.qdrant.coll)

    elif args.qdrant_index:
        qdrant_index()

    elif args.delete_index:
        db_handler.delItems()
    
    elif args.retrieve_id is not None:
        db_handler.retrieve_by_id(args.retrieve_id,True,True)

