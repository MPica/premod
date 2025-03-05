# -*- coding: utf-8 -*-
# DL IIIF

import re, os, time, json, requests, xmltodict, csv
from tqdm.notebook import tqdm
from PIL import Image
from lxml import etree as et
from pathlib import Path
from utils import A_navigation as nav

################################################################################################
# CHAINED DOWNLOADING PROCESS : 
def dlpics(project, dir_date):

    print("\n⏳ Importing the file list.\n")
    #txt_input = f"{proj_folder}/iiif_list.txt"
    iiifs = []
    with open(f"projects/{project}/iiif_manifests.txt") as filein:
        current = ""
        for line in tqdm(filein):
            if line != "\n":
                iiifs.append(line.strip())
    print("\nList of found URLs:\n")
    for document in iiifs:
        print(f"→{document}")

    print("\n⏳ Now downloading documents.\n")
    for document in tqdm(iiifs):
        dl_doc(document, dir_date)

################################################################################################
# DOWNLOAD ONE DOCUMENT.

def dl_doc(url, dir_date):

    if "https" not in url:
        print(f"{url} is not a valid URL, or not HTTPS secure.")

    else:
        recup = {}
        print(f"\tCurrently importing metadata for: {url}.")
        ark = "/".join(url.split("/")[-3:])
        ark_output = "_".join(ark.split("/")[-3:]).replace(":","")
        requete = requests.get(f"https://gallica.bnf.fr/iiif/{ark}/manifest.json")
        status = requete.status_code
        print(f"\t\t☞ {ark} → {status}")
        
        if status != 200:
            print(f"\t\t{ark} could not be imported.")

        else:
            allgood = True
            
            all_iiif_md = {}
            for item in requete.json()["metadata"]:
                label = item["label"].lower()
                val = item["value"]
                if label in all_iiif_md.keys():
                    all_iiif_md[label].append(val)
                else:
                    all_iiif_md[label] = [val]
            
            dc_md_r = requests.get(requete.json()["metadata"][3]["value"])
            dc_md_j = dc_md_r.text.replace('<?xml version="1.0" encoding="UTF-8" ?>',"")
            dc_md_d = xmltodict.parse(dc_md_j)
            
            if "date" in all_iiif_md.keys():
                date = sorted(all_iiif_md["date"])[0]
            else:
                date = "undated"
            
            """
            # For general use.
            if "author" in all_iiif_md.keys():
                date = "-".join(all_iiif_md["author"]).replace(" ","-")
            else:
                date = "noauthor"
            """
            
            # For OBJECTive use.
            colls = []
            ventes = []
            supp = [
                "[",
                "]",
                "(",
                ")",
                ".",
                " ",
                ",",
                " ",
                "Collection",
                "Art",
                "Vente"
            ]
            
            has_vente = False
            has_coll = False
            for desc in et.fromstring(dc_md_j).findall(".//{http://purl.org/dc/elements/1.1/}description"):
                if "collection" in desc.text.lower():
                    has_coll = True
                    coll = desc.text
                    suppd = [coll]
                    for char in supp:
                        mod = suppd[-1].replace(char, '')
                        suppd.append(mod)
                    collname = suppd[-1].replace(date,"").replace("-","")
                    colls.append(collname)
                    
                elif "vente" in desc.text.lower():
                    has_vente = True
                    ven = desc.text
                    suppd = [ven]
                    for char in supp:
                        mod = suppd[-1].replace(char, '')
                        suppd.append(mod)
                    venname = suppd[-1]
                    ventes.append(venname)
            
            if len(ventes) != 0:
                date = re.findall(r'\d{4}-\d{2}-\d{2}', sorted(ventes)[0])[0]
                
            if len(colls) != 0:
                book_name = f"{date}_{'_'.join(colls)}_{ark_output}"
            else:
                book_name = f"{date}_unknown-collector_{ark_output}"
            
            
            dir_catalogue = f"{dir_date}/{book_name}"
            dir_cat_short = f"{dir_date.split('/')[-1]}/{book_name}"
            dir_md = f"{dir_catalogue}/metadata"
            dir_wd = f"{dir_catalogue}/working_data"
            dir_wd_raw = f"{dir_catalogue}/working_data/raw"
            os.mkdir(dir_catalogue)
            os.mkdir(dir_md)
            os.mkdir(dir_wd)
            os.mkdir(dir_wd_raw)
            
            recup = {"folder": dir_wd_raw, "metadata":{"_comment":"This file contains the exact reproduction of the metadata gathered in the IIIF manifest of the source, and an automatic conversion of the OAI-PMH XML online file indicated there.","iiif":requete.json()["metadata"]}}
            recup["metadata"]["OAI-PMH"] = {}
            
            pnb = len(requete.json()['sequences'][0]['canvases'])
            print(f"\tDublin Core → {status}\n\tPages total → {str(pnb)}\n\tFolder name → {book_name}")
            
            with open(f"{dir_md}/{book_name}_manifest.json", "w") as jsonfile:
                json.dump(requete.json(), jsonfile)
            
            with open(f"{dir_md}/{book_name}_metadata.json", "w") as jsonfile:
                json.dump(recup["metadata"], jsonfile)
            
            mdroot = et.Element("metadata")
            mdroot.append(et.Comment("The present XML file contains an automatic XML conversion of the IIIF manifest metadata, and the direct reproduction of the OAI-PMH XML online file indicated there."))
            mdroot.append(parse_iiif(recup["metadata"]["iiif"]))
            mdroot.append(et.fromstring(dc_md_j))
            
            nav.write_xml(mdroot, f"{dir_md}/{book_name}_metadata.xml", "w")
            
            with open(f"{dir_md}/{book_name}_instructions.csv", "w") as csvfile:
                fieldnames = ["facsimile folder", "number of structuration levels", "first view", "last view", "skip from", "skip to"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerow({
                    "facsimile folder": f"{dir_cat_short}",
                    "number of structuration levels" : "0",
                    "first view" : "",
                    "last view" : "",
                    "skip from": "",
                    "skip to": ""
                })
            
            print(f"\tCurrently downloading images for: {url}.")
            pages = {}
            for count, page in tqdm(enumerate(requete.json()['sequences'][0]['canvases']), total=pnb):
                url = page["images"][0]["resource"]["@id"]
                extension = url.split(".")[-1]
                plabel = page["label"]
                path = f'{dir_wd_raw}/{book_name}_{str("{:04d}".format(count))}_{plabel}.{extension}'
                pages[url] = path
                dl_img(url, path)
                
                validity = False
                
                while validity == False:
                    dl_img(url, path)
                    validity = is_img_valid(path)
                    time.sleep(10)


################################################################################################
# DOWNLOAD AN ONLINE IMAGE AND SAVE IT LOCALLY

def dl_img(url, path):
    try:
        img_data = requests.get(url).content
        with open(path, 'wb') as handler:
            handler.write(img_data)
    except Exception as e:
        print(f"Failed to download {path} from {url}:")
        print(e)

################################################################################################
# CHECK IF A LOCAL IMAGE IS VALID

def is_img_valid(path):
    try:
        img = Image.open(path)
        img.verify()
        return True
    except:
        return False

################################################################################################
# Make an XML element from IIIF information


def parse_iiif(iiifmd):
    
    mdroot = et.Element("iiif")
    
    for el in iiifmd:
        if type(el["value"]) == str:
            mdroot.append(iiif_elem(el["label"], el["value"]))
        elif type(el["value"]) == list:
            for item in el["value"]:
                if type(item) == str:
                    mdroot.append(iiif_elem(el["label"], item))
                elif type(item) == dict:
                    mdroot.append(iiif_elem(el["label"], item["@value"]))
                else:
                    mdroot.append(et.Comment(json.dumps(item)))
    return mdroot


def iiif_elem(tag, value):
    element = et.Element(tag.replace(" ","_"))
    element.text = value
    return element