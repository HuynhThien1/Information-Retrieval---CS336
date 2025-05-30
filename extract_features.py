import pickle
from typing import Union
import numpy as np
import clip
import torch
import os
from torch import nn
from torch.utils.data import DataLoader
from tqdm import tqdm
from datetime import datetime
from data_utils import FashionIQDataset, targetpad_transform, CIRRDataset, data_path, server_base_path
from utils import collate_fn
from qdrant.img_data import ImageData
from PIL import Image
from pathlib import Path
from qdrant.provider import db_handler

#server_base_path = Path(__file__).absolute().parent.absolute().parent 


if torch.cuda.is_available():
    device = torch.device("cuda")
    data_type = torch.float16
else:
    device = torch.device("cpu")
    data_type = torch.float32

def extract_and_save_index_features(dataset: Union[CIRRDataset, FashionIQDataset], clip_model: nn.Module,
                                    feature_dim: int, file_name: str):
    """
    Extract CIRR or fashionIQ features (with the respective names) from a dataset object and save them into a file
    which can be used by the server
    :param dataset: dataset where extract the features
    :param clip_model: clip model used to extract the features
    :param feature_dim: feature dimensionality
    :param file_name: name used to save the features
    """
    val_loader = DataLoader(dataset=dataset, batch_size=32, num_workers=8, pin_memory=True,
                            collate_fn=collate_fn)
    index_features = torch.empty((0, feature_dim), dtype=torch.float16).to(device)
    index_names = []
    if isinstance(dataset, CIRRDataset):
        print(f"extracting CIRR {dataset.split} index features")
    elif isinstance(dataset, FashionIQDataset):
        print(f"extracting fashionIQ {dataset.dress_types} - {dataset.split} index features")

    # iterate over the dataset object
    for names, images in tqdm(val_loader):
        images = images.to(device)

        # extract and concatenate features and names
        with torch.no_grad():
            batch_features = clip_model.encode_image(images)
            index_features = torch.vstack((index_features, batch_features))
            index_names.extend(names)

    # save the extracted features
    data_path.mkdir(exist_ok=True, parents=True)
    torch.save(index_features, data_path / f"{file_name}_index_features.pt")
    with open(data_path / f'{file_name}_index_names.pkl', 'wb+') as f:
        pickle.dump(index_names, f)


def main():
    # define clip model and preprocess pipeline, get input_dim and feature_dim
    clip_model, clip_preprocess = clip.load("RN50x4")
    clip_model.eval()
    input_dim = clip_model.visual.input_resolution
    feature_dim = clip_model.visual.output_dim
    preprocess = targetpad_transform(1.25, input_dim)

    # extract and save cirr features
    cirr_val_dataset = CIRRDataset('val', preprocess)
    extract_and_save_index_features(cirr_val_dataset, clip_model, feature_dim, 'cirr_val')
    cirr_test_dataset = CIRRDataset('test1', preprocess)
    extract_and_save_index_features(cirr_test_dataset, clip_model, feature_dim, 'cirr_test')

    # extract and save fashionIQ features
    dress_types = ['dress', 'toptee', 'shirt']
    for dress_type in dress_types:
        val_dataset = FashionIQDataset('val', [dress_type], preprocess)
        extract_and_save_index_features(val_dataset, clip_model, feature_dim, f'fashionIQ_val_{dress_type}')
        test_dataset = FashionIQDataset('test', [dress_type], preprocess)
        extract_and_save_index_features(test_dataset, clip_model, feature_dim, f'fashionIQ_test_{dress_type}')


def qdrant_index():

    vector_idx = 0
    cirr_pt_file = [f for f in os.listdir(data_path) if 'cirr' in f and 'pt' in f]
    for f in cirr_pt_file:
        
        cirr_index_feature = torch.load(data_path / f, map_location=device).type(data_type).cpu()
        
        cirr_index_feature = cirr_index_feature.numpy()
        if 'test' in f:
            op = 'test1'
            with open(data_path / 'cirr_test_index_names.pkl', 'rb') as temp:
                cirr_index_name = pickle.load(temp)
        else:
            op = 'dev'
            with open(data_path / 'cirr_val_index_names.pkl', 'rb') as temp:
                cirr_index_name = pickle.load(temp)

        
        for idx, row in enumerate(cirr_index_feature):
            imgdata = ImageData(id= vector_idx,
                                index_date=datetime.now(),
                                image_vector=row,
                                thumbnail=cirr_index_name[idx],
                                dataset="cirr")
        
            try:
                img_path = os.path.join(server_base_path,'cirr_dataset',op,cirr_index_name[idx]+'.png')
                
                img = Image.open(img_path)
                imgdata.width = img.width
                imgdata.height = img.height
                imgdata.aspect_ratio = float(img.width) / img.height
            except:
                pass
            
            try:
                db_handler.insertItems(imgdata)
            except Exception as e:
                print(e)
                
            vector_idx += 1

    fashion_pt_file = [f for f in os.listdir(data_path) if  'fashion' in f and '.pt' in f]

    dress_types = ['dress', 'toptee', 'shirt']

    for f in fashion_pt_file:
        fashion_index_feature = torch.load(data_path / f, map_location=device).type(data_type).cpu()
        fashion_index_feature = fashion_index_feature.numpy()

        dress_type = [t for t in dress_types if t in f]
        if 'test' in f:
            with open(os.path.join(data_path,f"fashionIQ_test_{dress_type[0]}_index_names.pkl"),'rb') as temp:
                fashion_index_name = pickle.load(temp)

        elif 'val' in f:
            with open(os.path.join(data_path,f"fashionIQ_val_{dress_type[0]}_index_names.pkl"),'rb') as temp:
                fashion_index_name = pickle.load(temp)
        

        
        for idx, row in enumerate(fashion_index_feature):
            imgdata = ImageData(id= vector_idx,
                                index_date=datetime.now(),
                                image_vector=row,
                                thumbnail=fashion_index_name[idx],
                                dataset='fashionIQ')
            try:
                img_path = os.path.join(server_base_path,'fashionIQ_dataset','images',fashion_index_name[idx]+'.png')
                img = Image.open(img_path)
                imgdata.width = img.width
                imgdata.height = img.height
                imgdata.aspect_ratio = float(img.width) / img.height
            except:
                pass
        
            try:
                db_handler.insertItems(imgdata)
            except Exception as e:
                print(e)

            vector_idx += 1
    
        

if __name__ == '__main__':
    qdrant_index()