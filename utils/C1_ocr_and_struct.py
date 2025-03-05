# -*- coding: utf-8 -*-
# OCR AND STRUCT

import json
# import inference
from tqdm.notebook import tqdm
from pytesseract import pytesseract
# from inference_sdk import InferenceHTTPClient
import numpy as np
from utils import A_navigation as nav


################################################################################################
# CHAINED TRANSCRIPTION PROCESS : 

"""def pre_analysis(project, dir_date, OCRize, DataCat):

    if OCRize == True:
        img_to_alto(dir_date)

    if DataCat == True:
        datacat_analysis(dir_date)

    if OCRize == False:"""
        


################################################################################################
# CHAINED TRANSCRIPTION PROCESS : 

def img_to_alto(dir_date):

    err = []
    filerr = []
    count = 0
    
    file_dict = nav.parse_folders(dir_date)

    print("\n⏳ Now transcribing documents.\n")
    for source in tqdm(file_dict.keys()):
        transc = pytesseract_to_text(f"{source}/working_data/raw", file_dict[source], language)
        for er in transc["err"]:
            err.append(er)
        for f in transc["files"]:
            filerr.append(f)
        count += transc["count"]
    print("\n✅ All documents transcribed.\n")

    errunique = np.unique(err)
    print(f"\n{str(count)} errors occurred:")

    for erreur in errunique:
        print(f"\t{erreur}")
        print(f"\t\t{err.count(erreur)}")
        for nb, er in enumerate(err):
            if er == erreur:
                print(f"\t\t\t{filerr[nb]}")

################################################################################################
# LAYOUT ANALYSIS OF THE PAGES USING THE DATACATALOGUE MODEL.

def datacat_analysis(dir_date):
    
    file_dict = nav.parse_folders(dir_date)
    # model = inference.load_roboflow_model(model_id="macro-segmentation/10")
    
    for folder in tqdm(file_dict.keys()):

        ark = folder.split('/')[-1]
        print(f"\t☕ Now using the DataCat layout model on {ark}.")
        
        with open(f"{folder}/metadata/{ark}_manifest.json") as manifest:
            canvases = json.load(manifest)['sequences'][0]['canvases']
        
        for count, page in tqdm(enumerate(canvases), total=len(canvases)):
            url = page["images"][0]["resource"]["@id"]
            plabel = page["label"]
            path = f'{folder}/working_data/raw/{ark}_{str("{:04d}".format(count))}_{plabel}_datacat.json'
            results = model.infer(image=url)
            
            with open(path, "w") as jsonfile:
                json.dump(results, jsonfile)
            del results


################################################################################################
# TRANSCRIBE ONE DOCUMENT.

def pytesseract_to_text(folder, source, language):
    
    ark = folder.split("/")[-3]
    print(f"\n\t☕ Now transcribing: {ark}.")
    err = []
    filerr = []
    count = 0
    
    for file in tqdm(source):

        ext = file.split(".")[-1]
        if ext != "xml" and ext != "txt":
            name = ".".join(file.split(".")[:-1])
            
            try:
                nav.write_xml(pytesseract.image_to_alto_xml(f'{folder}/{file}', nice=1, lang=language), f"{folder}/{name}.xml", "wb")

                texte = pytesseract.image_to_string(f'{folder}/{file}', nice=1, lang=language)
                with open(f"{folder}/{name}.txt", "w") as outfile:
                    outfile.write(texte)
                    
            except Exception as e:
                count += 1
                err.append(str(e))
                filerr.append(f"{folder}/{file}")
                
    print(f"\t{count} errors on {ark}.")

    return {"count":count, "err":err, "files":filerr}

################################################################################################
# TRANSCRIBE A DOCUMENT WITH PERO-OCR.

#def pero_transc()