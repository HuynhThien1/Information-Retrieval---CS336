import json
import os
import pickle
import random
import time
from io import BytesIO
from multiprocessing import Process
from typing import Optional, Tuple, Union
import torch.nn.functional as F
import PIL.Image
import PIL.ImageOps
import clip
import numpy as np
import torch
from flask import Flask, send_file, url_for
from flask import render_template, request, redirect
from torchvision.transforms.functional import resize
from werkzeug.utils import secure_filename

from data_utils import targetpad_resize, targetpad_transform, server_base_path, data_path
from model import Combiner
from qdrant.provider import db_handler
from qdrant.query_params import FilterParams
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = server_base_path / 'uploaded_files'

if torch.cuda.is_available():
    device = torch.device("cuda")
    data_type = torch.float16
else:
    device = torch.device("cpu")
    data_type = torch.float32

global model


@app.route('/')

def model_choice():
    """
    Makes the render of dataset_choice template.
    """
    return render_template('model_choice.html')



@app.route('/favicon.ico')
def favicon():
    return url_for('static', filename='/favicon.ico')

@app.route('/<string:model>')
def dataset_choice(model):
    """
    Makes the render of dataset_choice template.
    """
    if model == 'image_retrieval':
        model = 'image_retrieval'
    elif model == 'text_retrieval':
        model = 'text_retrieval'
    elif model == 'compose':
        model = 'compose'

    return render_template('dataset_choice.html', model=model)
#This function is upload image don't add another
@app.route('/file_upload/<string:model>/<string:dataset>', methods=['POST'])
def file_upload(model: str, dataset: str):
    """
    Upload a reference image not included in the datasets
    :param dataset: dataset where upload the reference image
    """
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            return redirect(url_for('dataset_choice'))
        file = request.files['file']
        if file:
            try:
                img = PIL.Image.open(file)
            except Exception:  # If the file is not an image redirect to the reference choice page
                return redirect(url_for('reference', model=model, dataset=dataset))
            resized_img = resize(img, 512, PIL.Image.BICUBIC)

            filename = secure_filename(file.filename)
            filename = os.path.splitext(filename)[0] + str(int(time.time())) + os.path.splitext(filename)[
                1]  # Append the timestamp to avoid conflicts in names
            if 'fiq-category' in request.form:  # if the user upload an image to FashionIQ it must specify the category
                assert dataset == 'fashionIQ'
                fiq_category = request.form['fiq-category']
                folder_path = app.config['UPLOAD_FOLDER'] / dataset / fiq_category
                folder_path.mkdir(exist_ok=True, parents=True)
                resized_img.save(folder_path / filename)
            else:
                assert dataset == 'cirr'
                folder_path = app.config['UPLOAD_FOLDER'] / dataset
                folder_path.mkdir(exist_ok=True, parents=True)
                resized_img.save(folder_path / filename)

            return redirect(url_for('relative_caption', model=model, dataset=dataset, reference_name=filename))


@app.route('/<string:model>/<string:dataset>')
def reference(model: str, dataset: str):
    """
    Get 30 random reference images and makes the render of the 'reference' template
    :param dataset: dataset where get the reference images
    """
        
    if dataset == 'cirr':
        random_indexes = random.sample(range(len(cirr_val_triplets)), k=30)
        triplets = np.array(cirr_val_triplets)[random_indexes]
        names = [triplet['reference'] for triplet in triplets]
        text_names = [triplet['caption'] for triplet in triplets]
    elif dataset == 'fashionIQ':
        random_indexes = random.sample(range(len(fashionIQ_val_triplets)), k=30)
        triplets = np.array(fashionIQ_val_triplets)[random_indexes]
        names = [triplet['candidate'] for triplet in triplets]
        text_names = [triplet['captions'][0] for triplet in triplets]
    else:
        return redirect(url_for('choice'))
    if model == 'text_retrieval':
        return render_template('reference_caption.html', model=model, dataset=dataset, names=text_names)
    else:
        return render_template('reference.html', model=model, dataset=dataset, names=names)


@app.route('/<string:model>/<string:dataset>/<string:reference_name>')
def relative_caption(model: str, dataset: str, reference_name: str):
    """
    Get the dataset relative captions for the given reference image and renders the 'relative_caption' template
    :param dataset: dataset of the reference image
    :param reference_name: name of the reference images
    """
    if model == 'compose' or model == 'image_retrieval':
        relative_captions = []
        if dataset == 'cirr':
            for triplet in cirr_val_triplets:
                if triplet['reference'] == reference_name:
                    relative_captions.append(f"{triplet['caption']}")
        elif dataset == 'fashionIQ':
            for triplet in fashionIQ_val_triplets:
                if triplet['candidate'] == reference_name:
                    relative_captions.append(
                        f"{triplet['captions'][0].strip('?,. ').capitalize()} and {triplet['captions'][1].strip('?,. ')}")
    if model == 'compose':
        return render_template('relative_caption.html', model=model, dataset=dataset, reference_name=reference_name,
                           relative_captions=relative_captions)
    elif model == 'image_retrieval':
        return render_template('relative_image.html', model=model, dataset=dataset, reference_name=reference_name,
                           relative_captions=relative_captions)
    else:
        return render_template('relative_text.html', model=model, dataset=dataset, reference_name=reference_name)


@app.route('/<string:model>/<string:dataset>/<string:reference_name>/<string:old_caption>', methods=['POST'])
@app.route('/<string:model>/<string:dataset>/<string:reference_name>', methods=['POST'])
# @app.route('/<string:model>/<string:dataset>/<string:old_caption>', methods=['POST'])
def custom_caption(model: str, dataset: str, reference_name: Optional[str] = None, old_caption: Optional[str] = None):
    """
    Get the custom caption with a POST method and makes the render of 'results' template
    :param old_caption: caption of the previous query
    :param dataset: dataset of the query
    :param reference_name: reference image name
    """
    if reference_name is not None:
        print('reference', reference_name)
    else:
        print('old caption', old_caption)
    if  model == 'compose':
        caption = request.form['custom_caption']
        return redirect(url_for('results', model=model, dataset=dataset, reference_name=reference_name, caption=caption))
    elif model == 'image_retrieval':
        # reference_name = old_caption
        caption = request.form['custom_image']
        return redirect(url_for('results', model=model, dataset=dataset, reference_name=reference_name, caption=' '))
    else:
        caption = request.form['custom_caption']
        reference_name = caption
        global selection
        selection = ""
        if 'fashion_selection' in request.form:
            selection= request.form['fashion_selection']
            # print('selection', selection)
        return redirect(url_for('results', model=model, dataset=dataset, reference_name=reference_name, caption=caption))


@app.route('/<string:model>/<string:dataset>/<string:reference_name>/<string:caption>')
def results(model: str, dataset: str, reference_name: str, caption: str):
    """
    Compute the results of a given query and makes the render of 'results.html' template
    :param dataset: dataset of the query
    :param reference_name: reference image name
    :param caption: relative caption
    """
    n_retrieved = 50  # retrieve first 50 results since for both dataset the R@50 is the broader scale metric
    #select model 
    if model == 'compose':
        if dataset == 'cirr':
            combiner = cirr_combiner
        elif dataset == 'fashionIQ':
            combiner = fashionIQ_combiner
        else:
            raise ValueError()
    elif model == 'image_retrieval':
        combiner = clip_model
    elif model == 'text_retrieval':
        combiner = clip_model

    sorted_group_names = ""

    if dataset == 'cirr':
        # Compute CIRR results
        sorted_group_names, sorted_index_names, target_name = compute_cirr_results(caption, combiner, n_retrieved,
                                                                                   reference_name, model,search_option = 'qdrant')
    elif dataset == "fashionIQ":
        # Compute fashionIQ results
        sorted_index_names, target_name = compute_fashionIQ_results(caption, combiner, n_retrieved, reference_name, model, selection,search_option='qdrant')


    else:
        return redirect(url_for('choice'))
    
    #render templete
    if model == 'image_retrieval':
        return render_template('image_retrieval_results.html', model=model, dataset=dataset, caption=caption, reference_name=reference_name,
                           names=sorted_index_names[:n_retrieved], target_name=target_name,
                           group_names=sorted_group_names)
    elif model == 'text_retrieval':
        return render_template('text_retrieval_results.html', model=model, dataset=dataset, caption=caption, reference_name=reference_name,
                           names=sorted_index_names[:n_retrieved], target_name=target_name,
                           group_names=sorted_group_names)
    else:
        return render_template('results.html', model=model, dataset=dataset, caption=caption, reference_name=reference_name,
                           names=sorted_index_names[:n_retrieved], target_name=target_name,
                           group_names=sorted_group_names)



def compute_fashionIQ_results(caption: str, combiner: Combiner, n_retrieved: int, reference_name: str, model: str, selection: str, search_option:str) -> Tuple[
    np.array, str]:
    """
    Combine visual-text features and compute fashionIQ results
    :param caption: relative caption
    :param combiner: fashionIQ Combiner network
    :param n_retrieved: number of images to retrieve
    :param reference_name: reference image name
    :return: Tuple made of: 1)top 'n_retrieved' index names , 2) target_name (when known)
    """

    target_name = ""
    if model  == 'text_retrieval':
        dress_type = str(selection)
        print('selection', selection)
    # Assign the correct Fashion category to the reference image
    if model == 'compose' or model == 'image_retrieval':
        if reference_name in fashionIQ_dress_index_names:
            dress_type = 'dress'
        elif reference_name in fashionIQ_toptee_index_names:
            dress_type = 'toptee'
        elif reference_name in fashionIQ_shirt_index_names:
            dress_type = 'shirt'
        else:  # Search for an uploaded image
            for iter_path in app.config['UPLOAD_FOLDER'].rglob('*'):
                if iter_path.name == reference_name:
                    image_path = iter_path
                    dress_type = image_path.parent.name
                    break
            else:
                raise ValueError()

    # Check if the query belongs to the validation set and get query info
    if model == 'image_retrieval' or model == 'compose':
        for triplet in fashionIQ_val_triplets:
            if triplet['candidate'] == reference_name:
                if f"{triplet['captions'][0].strip('?,. ').capitalize()} and {triplet['captions'][1].strip('?,. ')}" == caption:
                    target_name = triplet['target']
                    dress_type = triplet['dress_type']

    # Get the right category index features
    if dress_type == "dress":
        if target_name == "":
            index_names = fashionIQ_dress_index_names
            index_features = fashionIQ_dress_index_features
        else:
            index_features = fashionIQ_val_dress_index_features.to(device)
            index_names = fashionIQ_val_dress_index_names
    elif dress_type == "toptee":
        if target_name == "":
            index_names = fashionIQ_toptee_index_names
            index_features = fashionIQ_toptee_index_features
        else:
            index_features = fashionIQ_val_toptee_index_features
            index_names = fashionIQ_val_toptee_index_names
    elif dress_type == "shirt":
        if target_name == "":
            index_names = fashionIQ_shirt_index_names
            index_features = fashionIQ_shirt_index_features
        else:
            index_features = fashionIQ_val_shirt_index_features
            index_names = fashionIQ_val_shirt_index_names
    else:
        raise ValueError()

    index_features = index_features.to(device)

    # Get visual features, extract textual features and compute combined features
    if model == 'compose' or model == 'image_retrieval':
        try:
            reference_index = index_names.index(reference_name)
            reference_features = index_features[reference_index].unsqueeze(0)
        except Exception:  # raise an exception if the reference image has been uploaded by the user
            image_path = app.config['UPLOAD_FOLDER'] / 'fashionIQ' / dress_type / reference_name
            pil_image = PIL.Image.open(image_path).convert('RGB')
            image = targetpad_transform(1.25, clip_model.visual.input_resolution)(pil_image).to(device)
            reference_features = clip_model.encode_image(image.unsqueeze(0))

    if model == 'compose' or model == 'text_retrieval':
        text_inputs = clip.tokenize(caption, truncate=True).to(device)
    if model == 'compose':
        with torch.no_grad():
            text_features = clip_model.encode_text(text_inputs)
            predicted_features = combiner.combine_features(reference_features, text_features).squeeze(0)
    elif model == 'image_retrieval':
        with torch.no_grad():
            predicted_features = reference_features.squeeze(0)
    elif model == 'text_retrieval':
        with torch.no_grad(): 
            predicted_features = clip_model.encode_text(text_inputs).squeeze(0)
    # Sort the results and get the top 50
    if search_option == 'torch':
        index_features = F.normalize(index_features)
        cos_similarity = index_features @ predicted_features.T
        sorted_indices = torch.topk(cos_similarity, n_retrieved, largest=True).indices.cpu()
        sorted_index_names = np.array(index_names)[sorted_indices].flatten()

    elif search_option == 'qdrant':
        filter_param = FilterParams(dataset='cirr')
        query_result = db_handler.query_search(predicted_features,filter_param=filter_param)
        sorted_index_names = np.array([point.img_data.thumbnail for point in query_result]).flatten()
    
    return sorted_index_names, target_name


def compute_cirr_results(caption: str, combiner: Combiner, n_retrieved: int, reference_name: str, model: str, search_option:str) -> Tuple[
    Union[list, object], np.array, str]:
    """
    Combine visual-text features and compute CIRR results
    :param caption: relative caption
    :param combiner: CIRR Combiner network
    :param n_retrieved: number of images to retrieve
    :param reference_name: reference image name
    :return: Tuple made of: 1) top group index names (when known) 2)top 'n_retrieved' index names , 3) target_name (when known)
    """
    target_name = ""
    group_members = ""
    sorted_group_names = ""

    index_features = cirr_index_features.to(device)
    index_names = cirr_index_names

    # Check if the query belongs to the validation set and get query info
    if model == 'compose':
        for triplet in cirr_val_triplets:
            if triplet['reference'] == reference_name and triplet['caption'] == caption:
                target_name = triplet['target_hard']
                group_members = triplet['img_set']['members']
                index_features = cirr_val_index_features.to(device)
                index_names = cirr_val_index_names

    # Get visual features, extract textual features and compute combined features
    if model == 'compose' or model == 'text_retrieval':
        text_inputs = clip.tokenize(caption, truncate=True).to(device)
    if model == 'compose' or model == 'image_retrieval':
        try:
            reference_index = index_names.index(reference_name)
            reference_features = index_features[reference_index].unsqueeze(0)
        except Exception:  # raise an exception if the reference image has been uploaded by the user
            image_path = app.config['UPLOAD_FOLDER'] / 'cirr' / reference_name
            pil_image = PIL.Image.open(image_path).convert('RGB')
            image = targetpad_transform(1.25, clip_model.visual.input_resolution)(pil_image).to(device)
            reference_features = clip_model.encode_image(image.unsqueeze(0))


    #compute predicted feature with three methods
    if model == 'compose':
        with torch.no_grad():
            text_features = clip_model.encode_text(text_inputs)
            predicted_features = combiner.combine_features(reference_features, text_features).squeeze(0)
    elif model == 'image_retrieval':
        with torch.no_grad():
            predicted_features = reference_features.squeeze(0)
    elif model == 'text_retrieval':
        with torch.no_grad():
            text_features = clip_model.encode_text(text_inputs)
            predicted_features = text_features.squeeze(0)

    # Sort the results and get the top 50
    if search_option == 'torch':
        index_features = F.normalize(index_features)
        cos_similarity = index_features @ predicted_features.T
        sorted_indices = torch.topk(cos_similarity, n_retrieved, largest=True).indices.cpu()
        sorted_index_names = np.array(index_names)[sorted_indices].flatten()

    elif search_option == 'qdrant':
        filter_param = FilterParams(dataset='cirr')
        query_result = db_handler.query_search(predicted_features,filter_param=filter_param)
        sorted_index_names = np.array([point.img_data.thumbnail for point in query_result]).flatten()
        print(sorted_index_names)
    if model == 'compose' or model == 'image_retrieval':
        sorted_index_names = np.delete(sorted_index_names, np.where(sorted_index_names == reference_name))

    # If it is a validation set query compute also the group results
    if model == 'compose':
        if group_members != "":
            if search_option == 'torch':
                group_indices = [index_names.index(name) for name in group_members]
                group_features = index_features[group_indices]
                cos_similarity = group_features @ predicted_features.T
                group_sorted_indices = torch.argsort(cos_similarity, descending=True).cpu()
                sorted_group_names = np.array(group_members)[group_sorted_indices]

            elif search_option == 'qdrant':
                group_filter_param = FilterParams(thumbnail_list=group_members, dataset='cirr')
                group_query_result = db_handler.query_search(predicted_features,filter_param=group_filter_param)
                sorted_group_names = np.array([point.img_data.thumbnail for point in group_query_result])
            sorted_group_names = np.delete(sorted_group_names, np.where(sorted_group_names == reference_name)).tolist()

    return sorted_group_names, sorted_index_names, target_name

@app.route('/get_image/<string:image_name>')
@app.route('/get_image/<string:image_name>/<int:dim>')
@app.route('/get_image/<string:image_name>/<int:dim>/<string:gt>')
@app.route('/get_image/<string:image_name>/<string:gt>')
def get_image(image_name: str, dim: Optional[int] = None, gt: Optional[str] = None):
    """
    get CIRR, FashionIQ or an uploaded Image
    :param image_name: image name
    :param dim: size to resize the image
    :param gt: if 'true' the has a green border, if 'false' has a red border anf if 'none' has a tiny black border
    """

    # Check whether the image comes from CIRR or FashionIQ dataset
    if image_name in cirr_name_to_relpath:  #
        image_path = server_base_path  /'cirr_dataset' / f'{cirr_name_to_relpath[image_name]}'
    elif image_name in fashion_index_names:
        image_path = server_base_path / 'fashionIQ_dataset' / 'images' / f"{image_name}.png"
    else:  # Search for an uploaded image
        for iter_path in app.config['UPLOAD_FOLDER'].rglob('*'):
            if iter_path.name == image_name:
                image_path = iter_path
                break
        else:
            raise ValueError()

    # if 'dim' is not None resize the image
    if dim:
        transform = targetpad_resize(1.25, int(dim), 255)
        pil_image = transform(PIL.Image.open(image_path))
    else:
        pil_image = PIL.Image.open(image_path)

    # add a border to the image
    if gt == 'True':
        pil_image = PIL.ImageOps.expand(pil_image, border=5, fill='green')
    elif gt == 'False':
        pil_image = PIL.ImageOps.expand(pil_image, border=5, fill='red')
    elif gt is None:
        pil_image = PIL.ImageOps.expand(pil_image, border=1, fill='grey')

    img_io = BytesIO()
    pil_image.save(img_io, 'JPEG', quality=80)
    img_io.seek(0)
    return send_file(img_io, mimetype='image/jpeg')


@app.before_first_request
def _load_assets():
    """
    Load all the necessary assets
    """

    app.config['UPLOAD_FOLDER'].mkdir(exist_ok=True, parents=True)
    p = Process(target=delete_uploaded_images)
    p.start()

    # load CIRR assets ---------------------------------------------------------------------------------------
    load_cirr_assets()

    # load FashionIQ assets ------------------------------------------------------------------------------
    load_fashionIQ_assets()

    # Load CLIP model and Combiner networks
    global clip_model
    global clip_preprocess
    clip_model, clip_preprocess = clip.load("RN50x4")
    clip_model = clip_model.eval().to(device)

    global fashionIQ_combiner
    fashionIQ_combiner = torch.hub.load(server_base_path, source='local', model='combiner', dataset='fashionIQ')
    fashionIQ_combiner = torch.jit.script(fashionIQ_combiner).type(data_type).to(device).eval()

    global cirr_combiner
    cirr_combiner = torch.hub.load(server_base_path, source='local', model='combiner', dataset='cirr')
    cirr_combiner = torch.jit.script(cirr_combiner).type(data_type).to(device).eval()


def load_fashionIQ_assets():
    """
    Load fashionIQ assets
    """
    global fashionIQ_val_triplets
    fashionIQ_val_triplets = []
    for dress_type in ['dress', 'toptee', 'shirt']:
        with open(server_base_path / 'fashionIQ_dataset' / 'captions' / f'cap.{dress_type}.val.json') as f:
            dress_type_captions = json.load(f)
            captions = [dict(caption, dress_type=f'{dress_type}') for caption in dress_type_captions]
            fashionIQ_val_triplets.extend(captions)

    global fashionIQ_val_dress_index_features
    fashionIQ_val_dress_index_features = torch.load(
        data_path / 'fashionIQ_val_dress_index_features.pt', map_location=device).type(data_type).cpu()

    global fashionIQ_val_dress_index_names
    with open(data_path / 'fashionIQ_val_dress_index_names.pkl', 'rb') as f:
        fashionIQ_val_dress_index_names = pickle.load(f)

    global fashionIQ_test_dress_index_features
    fashionIQ_test_dress_index_features = torch.load(
        data_path / 'fashionIQ_test_dress_index_features.pt', map_location=device).type(data_type).cpu()

    global fashionIQ_test_dress_index_names
    with open(data_path / 'fashionIQ_test_dress_index_names.pkl', 'rb') as f:
        fashionIQ_test_dress_index_names = pickle.load(f)

    global fashionIQ_dress_index_names
    global fashionIQ_dress_index_features
    fashionIQ_dress_index_features = torch.vstack(
        (fashionIQ_val_dress_index_features, fashionIQ_test_dress_index_features))
    fashionIQ_dress_index_names = fashionIQ_val_dress_index_names + fashionIQ_test_dress_index_names

    global fashionIQ_val_shirt_index_features
    fashionIQ_val_shirt_index_features = torch.load(
        data_path / 'fashionIQ_val_shirt_index_features.pt', map_location=device).type(data_type).cpu()

    global fashionIQ_val_shirt_index_names
    with open(data_path / 'fashionIQ_val_shirt_index_names.pkl', 'rb') as f:
        fashionIQ_val_shirt_index_names = pickle.load(f)

    global fashionIQ_test_shirt_index_features
    fashionIQ_test_shirt_index_features = torch.load(
        data_path / 'fashionIQ_test_shirt_index_features.pt', map_location=device).type(data_type).cpu()
    global fashionIQ_test_shirt_index_names
    with open(data_path / 'fashionIQ_test_shirt_index_names.pkl', 'rb') as f:
        fashionIQ_test_shirt_index_names = pickle.load(f)

    global fashionIQ_shirt_index_features
    global fashionIQ_shirt_index_names
    fashionIQ_shirt_index_features = torch.vstack(
        (fashionIQ_val_shirt_index_features, fashionIQ_test_shirt_index_features))
    fashionIQ_shirt_index_names = fashionIQ_val_shirt_index_names + fashionIQ_test_shirt_index_names

    global fashionIQ_val_toptee_index_features
    fashionIQ_val_toptee_index_features = torch.load(
        data_path / 'fashionIQ_val_toptee_index_features.pt', map_location=device).type(data_type).cpu()

    global fashionIQ_val_toptee_index_names
    with open(data_path / 'fashionIQ_val_toptee_index_names.pkl', 'rb') as f:
        fashionIQ_val_toptee_index_names = pickle.load(f)

    global fashionIQ_test_toptee_index_features
    fashionIQ_test_toptee_index_features = torch.load(
        data_path / 'fashionIQ_test_toptee_index_features.pt', map_location=device).type(data_type).cpu()

    global fashionIQ_test_toptee_index_names
    with open(data_path / 'fashionIQ_test_toptee_index_names.pkl', 'rb') as f:
        fashionIQ_test_toptee_index_names = pickle.load(f)

    global fashionIQ_toptee_index_features
    global fashionIQ_toptee_index_names
    fashionIQ_toptee_index_features = torch.vstack(
        (fashionIQ_val_toptee_index_features, fashionIQ_test_toptee_index_features))
    fashionIQ_toptee_index_names = fashionIQ_val_toptee_index_names + fashionIQ_test_toptee_index_names

    global fashion_index_features
    global fashion_index_names
    fashion_index_features = torch.vstack(
        (fashionIQ_dress_index_features, fashionIQ_shirt_index_features, fashionIQ_toptee_index_features))
    fashion_index_names = fashionIQ_dress_index_names + fashionIQ_shirt_index_names + fashionIQ_toptee_index_names


def load_cirr_assets():
    global cirr_val_triplets
    with open(server_base_path / 'cirr_dataset' / 'cirr' / 'captions' / f'cap.rc2.val.json') as f:
        cirr_val_triplets = json.load(f)

    global cirr_name_to_relpath
    with open(server_base_path / 'cirr_dataset' / 'cirr' / 'image_splits' / f'split.rc2.val.json') as f:
        cirr_name_to_relpath = json.load(f)
    with open(server_base_path / 'cirr_dataset' / 'cirr' / 'image_splits' / f'split.rc2.test1.json') as f:
        cirr_name_to_relpath.update(json.load(f))

    global cirr_val_index_features
    cirr_val_index_features = torch.load(data_path / 'cirr_val_index_features.pt', map_location=device).type(
        data_type).cpu()

    global cirr_val_index_names
    with open(data_path / 'cirr_val_index_names.pkl', 'rb') as f:
        cirr_val_index_names = pickle.load(f)

    global cirr_test_index_features
    cirr_test_index_features = torch.load(data_path / 'cirr_test_index_features.pt', map_location=device).type(
        data_type).cpu()

    global cirr_test_index_names
    with open(data_path / 'cirr_test_index_names.pkl', 'rb') as f:
        cirr_test_index_names = pickle.load(f)

    global cirr_index_features
    global cirr_index_names
    cirr_index_features = torch.vstack((cirr_val_index_features, cirr_test_index_features))
    cirr_index_names = cirr_val_index_names + cirr_test_index_names


def delete_uploaded_images():
    '''
    For privacy reasons delete the uploaded images after 500 seconds
    '''
    FILE_LIFETIME = 500
    SLEEP_TIME = 50
    while True:
        for iter_path in app.config['UPLOAD_FOLDER'].rglob('*'):
            if iter_path.is_file():
                if time.time() - iter_path.stat().st_mtime > FILE_LIFETIME:
                    iter_path.unlink()

        time.sleep(SLEEP_TIME)


if __name__ == '__main__':
    # test_text_search()
    app.run(host="0.0.0.0", port=5000)
