<!-- Banner -->
<p align="center">
  <a href="https://www.uit.edu.vn/" title="Trường Đại học Công nghệ Thông tin" style="border: none;">
    <img src="https://i.imgur.com/WmMnSRt.png" alt="Trường Đại học Công nghệ Thông tin | University of Information Technology">
  </a>
</p>
<h1 align="center"><b>TRUY VẤN THÔNG TIN ĐA PHƯƠNG TIỆN</b></h>

## THÀNH VIÊN NHÓM

| STT |   MSSV   |       Họ và Tên |                     Github                                 |            Email                        |
| --- | :------: | --------------: |  --------------------------------------------------------: | ---------------------------------------:|
| 1   | 21522634 |  Lê Chí Thịnh   |  [lechithinh](https://github.com/lechithinh)               | 21522634@gm.uit.edu.vn                  |
| 2   | 21522621 | Huỳnh Công Thiện|  [HuynhThien1](https://github.com/HuynhThien1)             | 21522621@gm.uit.edu.vn                  |
| 3   | 21522706 | Nguyễn Minh Trí |  [MinhTri17](https://github.com/MinhTri17)                 | 21522706@gm.uit.edu.vn                  |


## GIỚI THIỆU MÔN HỌC

-   **Tên môn học:** Truy vấn thông tin đa phương tiện
-   **Mã môn học:** CS336
-   **Mã lớp:** CS336.O12.KHCL
-   **Năm học:** HK2 (2023 - 2024)
-   **Giảng viên**: TS.Đỗ Văn Tiến


# Image retrieval System

We are thrilled to introduce our cutting-edge image retrieval system that is powered by advanced algorithms and state-of-the-art machine learning techniques. This remarkable system represents a significant leap forward in the field of image searches, offering users effortless access to highly precise results. It is with great pleasure that we bid farewell to the cumbersome task of endless scrolling and welcome an exciting new era of image discovery.

## Features



## Technology

Here are the techs we implemented for this project

-  [Python](https://docs.python.org/3/)
-  [Flask](https://flask.palletsprojects.com/en/3.0.x/)
-  [Pytorch](https://pytorch.org/vision/main/models/generated/torchvision.models.vgg16.html#torchvision.models.VGG16_Weights)

## Installation
Clone the repository

```sh
git clone https://github.com/HuynhThien1/Information-Retrieval---CS336.git
```
```sh
conda create -n clip4cir -y python=3.8
conda activate clip4cir
conda install -y -c pytorch pytorch=1.7.1 torchvision=0.8.2
pip install flask==2.0.2
pip install git+https://github.com/openai/CLIP.git
pip install Werkzeug==2.0.1
```sh
## Structure

Please organize your code following this structure: 

```
```
project_base_path
└───  fashionIQ_dataset
      └─── captions
            | cap.dress.test.json
            | cap.dress.train.json
            | cap.dress.val.json
            | ...
            
      └───  images
            | B00006M009.jpg
            | B00006M00B.jpg
            | B00006M6IH.jpg
            | ...
            
      └─── image_splits
            | split.dress.test.json
            | split.dress.train.json
            | split.dress.val.json
            | ...

└───  cirr_dataset       
       └─── dev
            | dev-0-0-img0.png
            | dev-0-0-img1.png
            | dev-0-1-img0.png
            | ...
       
       └─── test1
            | test1-0-0-img0.png
            | test1-0-0-img1.png
            | test1-0-1-img0.png 
            | ...
       
       └─── cirr
            └─── captions
                | cap.rc2.test1.json
                | cap.rc2.train.json
                | cap.rc2.val.json
                
            └─── image_splits
                | split.rc2.test1.json
                | split.rc2.train.json
                | split.rc2.val.json
```
```
