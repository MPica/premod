# -*- coding: utf-8 -*-
# NAVIGATION

import os, time, re
from lxml import etree as et
from datetime import datetime
from io import BytesIO
from pathlib import Path

################################################################################################

# GENERATE A PROJECT FOLDER TO ENSURE ALL IS THERE

def new_project(name):

    current = os.getcwd()

    # Modify the project name in case it is not UTF-7 compatible.
    for char in ".,?;:/!":
        name = name.lower().replace(char, "")
    name = re.sub(r'[àáâãäå]', 'a', name)
    name = re.sub(r'[èéêë]', 'e', name)
    name = re.sub(r'[ìíîï]', 'i', name)
    name = re.sub(r'[òóôõö]', 'o', name)
    name = re.sub(r'[ùúûü]', 'u', name)
    name = re.sub(r'\s', '_', name)
    name = re.sub(r'_+', '_', name)
    name = re.sub(r'_$', '', name)
    name = re.sub(r'^_', '', name)
    
    projdir = f"{current}/projects/{name}"

    if os.path.exists(projdir):
        print("A project folder under this name already exists.")
    else:
        os.mkdir(projdir)
        os.mkdir(projdir+"/input")
        os.mkdir(projdir+"/output")
        os.mkdir(projdir+"/classification")

    iiifs = "# Please enter one link per line.\n# If you need to sort the links, please know\n# that lines beginning with a # sign\n# as well as empty lines will be ignored."

    with open(f"{projdir}/iiif_manifests.txt", "w") as txtfile:
        txtfile.write(iiifs)


################################################################################################

# LIST ALL FILES IN WORKING FOLDERS
# FROM IIIF ONLY

def parse_folders(onedir, iiif = False):
    
    file_dict = {}
    
    for folder in os.listdir(onedir):
        path = f'{onedir}/{folder}'
        if Path(path).is_dir() == True and "checkpoint" not in folder:
            file_dict[path] = [f.name for f in os.scandir(f'{path}/working_data/raw') if f.is_file()]
        
    return file_dict

################################################################################################

# MKDIR FROM TIMESTAMP

def mk_tmsp_dir(target_location, project=""):
    # Get current time
    dt = datetime.now()
    tmsp = dt.strftime("%Y%m%d_%H%M")
    projdir = f"{target_location}/projects/{project}/output"

    # Construct the path for outputs. 
    if project == "":
        print("WARNING: You must define and create a project folder in the 'projects' folder.")
    else:
        if os.path.exists(projdir) == False:
            os.mkdir(projdir)
        dir_date = f"{target_location}/projects/{project}/output/extraction_{tmsp}"
    
    os.mkdir(dir_date)

    return dir_date

################################################################################################

# WRITE AN XML FILE TO DISC

def write_xml(tree, location, mode):
    
    useless_tei = re.compile(r' xmlns:ns\d+="http://www.tei-c.org/ns/1.0"')
    useless_att = re.compile(r'ns\d+:')
    
    to_write = et.tostring(tree, xml_declaration=True, encoding="utf-8", pretty_print = False).decode('UTF-8')
    nscorr = useless_att.sub('', useless_tei.sub('', to_write)).replace('<TEI>', '<TEI xmlns:"http://www.tei-c.org/ns/1.0"')
        
    with open(location, mode) as xmlfile:
        xmlfile.write(nscorr)