import json
import os
import time
from _csv import writer
from copy import deepcopy
from os.path import basename
import numpy as np
import cv2
import uuid
import requests
from pdf2image import convert_from_path
import shutil
from portal import APP

import sys

from PIL import Image
import cv2
import threading, queue
import datetime
from .cloud_connection import S3CONNECTION


def pdfapilocal(filename):
    # print('49')
    # print(str(request.files.getlist('file')))
    # print('52')
    # file1 = open(filename)
    # print(file1)
    if True:
        print('54')
        print(filename)
        # filename = secure_filename(filename)
        # if not os.path.isdir('/classification-API/incomings'):
        #     os.mkdir('/classification-API/incomings')
        random_id = str(uuid.uuid4())
        os.mkdir(BASE_IMGS_FOLDER + '/' + random_id)
        folder = BASE_IMGS_FOLDER + '/' + random_id
        root_path = "./extract"
        hospital_identified = 'none'
        ##pt.pytesseract.tesseract_cmd = "./tesseract/tesseract.exe"
        # path = "./listen/" + pdf_filename
        save_path = folder
        # file1[0].save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        # eachfilepath = os.path.join(UPLOAD_FOLDER, filename)
        converting_to_image(filename, save_path, folder)
        resp = seggregator(save_path)
        # print(str(resp[0]))
        # print(str(resp[1]))
        # print(str(resp[2]))
        print('72')
        # print(resp[3])
        responses = {'hospital': resp[0], 'documents': resp[2]}
        # responses['counts'] = resp[3]
        print(type(responses))
        resplist = []
        # resplist.append(responses)
        # resplist.append(resp[3])
        # print(type(resp[3]))
        return responses
    else:
        print('error')
        errors[file1[0].filename] = 'File type is not allowed'
    return 'ok'
# 666

def change_resolution(input_image_path, output_image_path, basewidth, baseheight):
    # img = Image.open(input_image_path)
    # # baseheight = data["baseheight"]
    # # basewidth = data["basewidth"]
    # hpercent = (baseheight / float(img.size[1]))
    # wsize = int((float(img.size[0]) * float(hpercent)))
    # wpercent = (basewidth / float(img.size[0]))
    # hsize = int((float(img.size[1]) * float(wpercent)))
    # print(wsize, hsize)
    # img = img.resize((wsize, hsize), Image.ANTIALIAS)
    # img.save(output_image_path)
    image = cv2.imread(input_image_path, 1)
    resized_image = cv2.resize(image, (basewidth, baseheight))
    cv2.imwrite(output_image_path, resized_image)


def text_concat(json_data):
    text = " ".join([str(text.get('text')) for text in json_data])
    return text


def icr_conn(subscription_key, endpoint, image_path):
    text_recognition_url = endpoint + ""
    image_data = open(image_path, "rb").read()
    headers = {'Ocp-Apim-Subscription-Key': subscription_key,
               'Content-Type': 'application/octet-stream'}
    params = {'visualFeatures': 'Categories,Description,Color'}
    response = requests.post(
        text_recognition_url, headers=headers, params=params, data=image_data)

    response.raise_for_status()
    operation_url = response.headers["Operation-Location"]

    analysis = {}
    poll = True
    while poll:
        response_final = requests.get(
            response.headers["Operation-Location"], headers=headers)
        analysis = response_final.json()
        time.sleep(1)
        if "recognitionResults" in analysis:
            poll = False
        if "status" in analysis and analysis['status'] == 'Failed':
            poll = False
    text_json = analysis['recognitionResults'][0].get("lines")
    return text_json



def get_icr_data(image_url):
   
    image_url_changed = str(image_url).replace("?","")
    url = ""
    payload={'image_url': str(image_url_changed)}
    files=[
    ]
    headers = {}
    response = requests.request("POST", url, headers=headers, data=payload, files=files, verify=True)
    return response.json()

def get_icr_data_from_image(filepath: str,q2):
    
    image_path = filepath
    sys_date = str(datetime.datetime.now()).split(".")[0]
    file_name_to_save = sys_date.replace(":", "_").replace(" ", "")
    S3CONNECTION.upload_to_aws(image_path,"/" + file_name_to_save + "/" + str(image_path).split("/")[len(str(image_path).split("/")) - 1])
    image_url = S3CONNECTION.image_presigned_url("/" + file_name_to_save + "/" + str(image_path).split("/")[len(str(image_path).split("/")) - 1])
    print(image_url, "urls")
    #app.logger.info(str(image_url))
    text_json = get_icr_data(image_url)
    #app.logger.info(str(text_json))
    data = {
                                        "json_text": text_json
           }
    q2.put(data)



def save_image_of_pdf(page,length_of_files_present,i,save_path,folder,q1):
    page.save(os.path.join(save_path, basename(folder + str(i + 1 + length_of_files_present) + '.jpg')), 'JPEG')
    # img = cv2.imread(os.path.join(save_path, str(i + length_of_files_present) + '.jpg'))
    change_resolution(os.path.join(save_path, basename(folder + str(i + 1 + length_of_files_present) + ".jpg")),
                      os.path.join(save_path, basename(folder + str(i + 1 + length_of_files_present) + ".jpg")),2300, 2700)
    data = {
        "result":"ok"
    }
    q1.put(data)

def converting_to_image(file_name, save_path, folder):
    file_name_temp = []
    my_image_name = str(file_name).replace(".PDF", "").replace(".pdf", "")
    length_of_files_present = len(os.listdir(save_path))

    print(length_of_files_present)

    ##print("Started")
    ##my_image_name1 = my_image_name.split("\\")[-1]
    ##print(my_image_name1)
    doc_name = []
    # import tempfile
    # with tempfile.TemporaryDirectory() as tempdir:
    start = time.time()
    pages = convert_from_path(file_name)
    print("convert",time.time() - start)
    print("Started Image Extraction....")
    no_of_pages = len(pages)
    print("pages : ", no_of_pages)
    queue_variables = {}
    for i in range(len(pages)):
        queue_variables["new_data_" + str(i)] = queue.Queue()
        ##file_name_temp.append(str(my_image_name) + '-' + str(i) + '.jpeg')
        ##pages[i].save(save_path + str(i) + '.jpeg', 'JPEG')
        ##file_name_temp.append(save_path + str(i) + '.jpeg')
        # filepath = os.path.join(folder, str(i + length_of_files_present) + ".jpg")
        # pages[i].save(os.path.join(save_path, basename(folder + str(i + 1 + length_of_files_present) + '.jpg')), 'JPEG')
        # # img = cv2.imread(os.path.join(save_path, str(i + length_of_files_present) + '.jpg'))
        # change_resolution(os.path.join(save_path, basename(folder + str(i + 1 + length_of_files_present) + ".jpg")),
        #                   os.path.join(save_path, basename(folder + str(i + 1 + length_of_files_present) + ".jpg")),
        #                   2300, 2700)
        threading.Thread(target=save_image_of_pdf,args=(pages[i],length_of_files_present,i,save_path,folder,queue_variables["new_data_" + str(i)],)).start()
    for i in range(len(pages)):
        result = queue_variables["new_data_" + str(i)].get()


    print('completed imaging')
    # print(doc_name)
    ##file_name_temp.append(os.path.join(save_path,str(i) + '.jpeg'))
    # return hospital, doc



def seggregator(path, random_id):
    ###takes path of folder containing images as input and starts finding hospital first and docs next
    print('length:')
    print(len(os.listdir(path)))
    hospital_ = 'none'
    documents_indexes = []
    documents_indexes_dict = {}
    document_names = []
    documents = {}
    extracts = {}
    json_datas = {}
    queue_variables = {}
    start = time.time()
    for i in range(1, len(os.listdir(path)) + 1):
        # try:
        queue_variables["icr_data_" + str(i)] = queue.Queue()
        filepath = os.path.join(path, basename(path + str(i) + ".jpg"))

        # text = get_icr_data_from_image(filepath,basename(path + str(i) + ".jpg"),queue_variables["icr_data_" + str(i)])
        threading.Thread(target=get_icr_data_from_image,
                         args=(filepath, queue_variables["icr_data_" + str(i)],)).start()
    print("icr_init completed", time.time() - start)
    start = time.time()
    for i in range(1, len(os.listdir(path)) + 1):
        result = queue_variables["icr_data_" + str(i)].get()
        print(result)
        text = result['json_text']
        filepath = os.path.join(path, basename(path + str(i) + ".jpg"))
        json_datas[basename(filepath)] = text
        text_json = text_concat(text)

        extracts[basename(filepath)] = text_json
    print("icr get data completed", time.time() - start)
    with open('all_bill.json', 'w') as f:
        json.dump(json_datas, f)
        # f.write(str(json_datas))

    for h in extracts:
        print('started hospitals')

        hospital_ = hospitalfinder(extracts[h])

        if hospital_ != 'none':
            break
    print('107: ' + hospital_)
    # finding hospital ends here
    counter = 0
    for j in extracts:
        # nums = []
        # filepath = os.path.join(folder, str(j) + ".jpeg")
        # text = get_icr_data_from_image(filepath)
        # text_json = text_concat(text)
        # print(text_json + '\n\n8989\n\n')
        print('197')
        print(random_id)
        print("j:", j)
        doc = classifier(extracts[j], 2, hospital_)
        # nums.append(str(j))
        documents_indexes.append(str(counter + 1) + ": ")
        documents_indexes.append(doc)

        documents_indexes_dict[str(counter + 1)] = doc  # here new code for dict

        document_names.append(doc)

        documents[basename(j)] = doc

        counter = counter + 1

    print("documents_indexes_dict: ", documents_indexes_dict)
    print("document_names: ", document_names)
    print("documents: ", documents)

    print('112: ' + hospital_)
    for i in range(len(document_names)):
        print(document_names[i] + '\n')
        if document_names[i] == 'unknown':
            if len(document_names) - 1 > i > 0:
                if document_names[i - 1] == document_names[i + 1]:
                    # print('166')
                    # print(i-1)
                    # print(document_names[i-1])
                    # print(document_names[i+1])
                    # print(i+1)
                    # print('166')
                    document_names[i] = document_names[i - 1]
                    documents_indexes[2 * i + 1] = document_names[i - 1]
                    documents[basename(path + str(i + 1) + ".jpg")] = deepcopy(
                        documents[basename(path + str(i + 1) + ".jpg")])

    print(document_names)
    print(documents_indexes)
    unq, counts = np.unique(np.array(document_names), return_counts=True)
    frequencies = dict(zip(unq, counts))
    print(frequencies)

    """ old code
    ress = {'hospital': hospital_,
            'documents:': documents_indexes
            }
    """

    ress = {'hospital': hospital_,
            'documents': documents_indexes_dict
            }

    print('175')
    print(ress)

    return ress



def hospitalfinder(txt: str):
    print('122 \n\n')
    # print(txt)
    print(txt)
    print("\n\n138")
    hospital_local = 'none'
    commonvar = txt.lower().replace(" ", "")
    print(txt)
    if txt.lower().replace(" ", "").__contains__('textofhospital'):
        hospital_local = ''
    # elif ('medanta-themedicity' in commonvar or 'medantha' in commonvar and not '09aaicm9846k1zn' in commonvar):
    #     hospital_local = 'medanta'
    elif (txt.lower().replace(" ", "").__contains__('') or txt.lower().replace(" ", "").__contains__('medantha')) and not ('medanta-lucknow' in commonvar or '09aaicm9846k1zn' in commonvar):
        hospital_local = ''
    else:
        hospital_local = None
    
    return hospital_local







def classifier(txt: str, c: int, hosp: str):
    if hosp == '':
        present = {
            
        }

        absent = {
            
        }
    elif hosp == '':
        present = {
            
                   
        }

        absent = {

          


        }
    else:
       
        present = {
            
                   
        }

        absent = {

          
          

        }
    





    """classification of doc starts here"""
    count = 0
    document = 'none'
    document_final = 'unknown'

    documents = []
    hospitals = []

    print('98')
    
    #     hospital = 'blk'
    for key in present.keys():
        # print('into the present dictionary')
        count = 0
        for i in present[key]:
            # print('into the keywords of '+key)
            # print(i + '\n')
            if txt.lower().replace(" ", "").__contains__(i):
                count = count + 1
                print(i)
                print('doc: ' + key)
                if count >= c:
                    print('117')
                    document = key
                    print('138 ' + document)
                    print(key)
                    for j in absent[key]:
                        # print('into the absent keywords of '+key)
                        # print('141 ' + key)
                        if txt.lower().replace(" ", "").__contains__(j):
                            count = 0
                            print('Exceptions:')
                            print(j)
                            document = 'none'
                            break
                    if count >= c:
                        break
        if count >= c:
            print('148')
            print(document)
            document_final = document
            # documents.append(document)
            break
    print('list:\n')
    print(document_final)
    return document_final


