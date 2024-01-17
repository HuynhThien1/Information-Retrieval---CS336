import boto3
import os
from data_utils import server_base_path

s3 = boto3.client('s3')
# s3.upload_file('E:\\UIT\\UIT_HK_V\\TVTTDPT\\doan\\Information-Retrieval---CS336\\cirr_dataset\\test1\\test1-0-0-img0.png','myirsbucket','cirr_dataset/test1/test1-0-0-img0.png')
BUCKET_NAME = 'myirsbucket'
cirr_data_path = os.path.join(server_base_path,'cirr_dataset')
fashion_iq = os.path.join(server_base_path,'fashionIQ_dataset')

# cirr_folder = ['dev','test1']
# for f in cirr_folder:
#     folder_path = os.path.join(cirr_data_path,f)
#     for img in os.listdir(folder_path):
#         print(img)
#         des_folder = f'cirr_dataset/{f}/{img}'
#         img_path = os.path.join(folder_path,img)
#         s3.upload_file(img_path,BUCKET_NAME,des_folder)

for img in os.listdir(os.path.join(fashion_iq,'images')):
    des_folder = f'fashionIQ_dataset/images/{img}'
    img_path = os.path.join(os.path.join(fashion_iq,'images'),img)
    s3.upload_file(img_path,BUCKET_NAME,des_folder)

