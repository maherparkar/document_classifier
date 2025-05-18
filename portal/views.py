import json
import os
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, send_file,  \
    Response, jsonify
import threading
from . import APP, LOG
from api_classification import pdfapilocal,change_resolution,text_concat,get_icr_data_from_image,converting_to_image,seggregator, hospitalfinder,classifier
from flask import Flask, jsonify,request,json
import os
from werkzeug.utils import secure_filename
from werkzeug.exceptions import BadRequest
import shutil
import uuid
import numpy as np
import glob


bp = Blueprint('view', __name__, url_prefix='/classification_call')



def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in APP.config['ALLOWED_EXTENSIONS']


@bp.route('/')
def main():
    return 'Classification'


@bp.route('/upload',methods= ['POST'])
def upload_file():
    MAIN_DIR = "uploads"
    filelist = glob.glob(os.path.join(MAIN_DIR, "*"))


    for f in filelist:
        os.remove(f)
        print("donme")
    BASE_IMGS_FOLDER = APP.config['BASE_IMGS_FOLDER']
    for file_imgs in os.listdir(BASE_IMGS_FOLDER):
        file_path = os.path.join(BASE_IMGS_FOLDER,file_imgs)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Fazlied')



    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            return BadRequest("No File")
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            # flash('No selected file')
            return BadRequest("No File")
        if not allowed_file(file.filename):
            return BadRequest("File Not Allowed")
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(APP.config['UPLOAD_FOLDER'], filename))
            path_to_watch = os.path.join("./uploads")

            token = 1
            while token:
                if 1:



                    random_id = str(uuid.uuid4())
                    os.mkdir(BASE_IMGS_FOLDER + '/' + random_id)
                    folder = BASE_IMGS_FOLDER + '/' + random_id
                    root_path = "./extract"
                    hospital_identified = 'none'
                    save_path = folder
                    i = 0


                    for filename in os.listdir(MAIN_DIR):

                        print(filename)
                        eachfilepath = os.path.join(MAIN_DIR, filename)
                        converting_to_image(eachfilepath, save_path, folder)
                    output=seggregator(save_path, random_id)
                    print(output,"asdfghjkl")
                    token = 0
                    # os.remove(os.path.join(r"uploads/" + str(filename) + ""))
                    # print("done")
                    # shutil.rmtree(os.path.join(r"imgsfolder/" + str(random_id) + ""))
                    # print("done2")
            return output


            # except:
            #     save_path = path_to_watch
            #     result, documents, json_datas = seggregator(save_path, random_id)
            #     originalfilepath = os.path.join(path_to_watch, os.listdir(path_to_watch)[0])
            #     BASE_IMGS_FOLDER = r"imgsfolders"
            #     targetfilepath = os.path.join(folder, os.listdir(path_to_watch)[0])
            #     shutil.copyfile(originalfilepath, targetfilepath)



