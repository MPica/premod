# -*- coding: utf-8 -*-

import json, os, csv, json
import lxml.etree as et
import numpy as np
from tqdm.notebook import tqdm
from utils import A_navigation as nav

#####################################################################################
# MAIN

def centralize_alto(dir_date):
    
    print("\n⏳ Now compiling raw transcription files.")
    
    nsmap = {
        None: "http://www.tei-c.org/ns/1.0",
        "alto": "http://www.loc.gov/standards/alto/ns-v3#",
        "oai-pmh": "http://www.openarchives.org/OAI/2.0/",
        "dc": "http://purl.org/dc/elements/1.1/",
        "oai_dc": "http://www.openarchives.org/OAI/2.0/oai_dc/",
        "xml":"http://www.w3.org/XML/1998/namespace"
    }
    
    file_dict = nav.parse_folders(dir_date)
    
    for folder in tqdm(file_dict.keys()):
        
        ark = folder.split('/')[-1]
        print(f"\t☕ Now compiling {ark}.")
        
        local = sorted(file_dict[folder])
        lines = {}
        tokens = []
        alto = et.Element("{http://www.loc.gov/standards/alto/ns-v3#}alto", nsmap=nsmap)
        layout_all = et.SubElement(alto, "{http://www.loc.gov/standards/alto/ns-v3#}Layout", nsmap=nsmap)
        md_folder = f"{folder}/metadata"
        recap_folder = f"{folder}/working_data/recap"
        try:
            os.mkdir(recap_folder)
        except:
            print(f"{recap_folder} already exists.")
        filist = []
        
        for file in local:
            if ".".join(file.split(".")[:-1]) not in filist:
                filist.append(".".join(file.split(".")[:-1]))
        
        skip = []
        levels =  0
        first = ""
        last = ""
        with open(f"{md_folder}/{ark}_instructions.csv") as csvfile:
            instructions = csv.DictReader(csvfile)
            for count, row in enumerate(instructions):
                
                if count == 0:
                    levels = int(row["number of structuration levels"])
                    first = row['first view']
                    last = row['last view']
                
                if row['skip from'] != '' and row['skip from'] is not None:
                    if row['skip to'] != '' and row['skip to'] is not None:
                        for file in span_2_list(filist, row['skip from'], row['skip to'])['actual files']:
                            if file not in skip:
                                skip.append(file)
                    else:
                        skip.append(row['skip from'])
        
        front = {}
        back = {}
        span2list = span_2_list(filist, first, last)
                
        for file in filist:

            with open(f"{folder}/working_data/raw/{file}.xml") as onexml:
                tree = et.parse(onexml)
                root = tree.getroot()
            
            reidd = re_id(file, root)
            for token in tesstokens(reidd, file):
                thisline = token['line']
                
                if file in span2list['actual files'] and file not in skip:
                    tokens.append(token)
                    if thisline in lines.keys():
                        lines[thisline]['tokens'].append(token['text'])
                        lines[thisline]['ids'].append(token['string'])
                    else:
                        lines[thisline] = {'tokens':[token['text']], 'ids': [token['string']]}
                        
                elif file in span2list['before']:
                    if thisline in front.keys():
                        front[thisline]['tokens'].append(token['text'])
                        front[thisline]['ids'].append(token['string'])
                    else:
                        front[thisline] = {'tokens':[token['text']], 'ids': [token['string']]}
                
                elif file in span2list['after']:
                    if thisline in back.keys():
                        back[thisline]['tokens'].append(token['text'])
                        back[thisline]['ids'].append(token['string'])
                    else:
                        back[thisline] = {'tokens':[token['text']], 'ids': [token['string']]}

                        
            for page in reidd.findall('.//{http://www.loc.gov/standards/alto/ns-v3#}Page'):
                layout_all.append(page)
        
        nav.write_xml(alto, f'{recap_folder}/{ark}_full_alto.xml')
        
        with open(f'{recap_folder}/{ark}_front_and_back.json', 'w') as jsonfile:
            json.dump({"front":front, "back":back}, jsonfile)
            
        with open(f'{recap_folder}/{ark}_separate_lines.csv', 'w') as csvfile:
            fieldnames = []
            countlvls = 0
            while countlvls < levels:
                countlvls += 1
                fieldnames.append(f"title level {str(countlvls)}")
            fieldnames.extend(["paragraph beginning", "text", "page", "line id", "text ids"])
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for line in lines.keys():
                countlvls = 0
                row = {
                    "paragraph beginning":"",
                    "text" : " ".join(lines[line]['tokens']),
                    "page" : line.split("_")[6],
                    "line id" : line,
                    "text ids" : " ".join(lines[line]['ids'])
                }

                while countlvls < levels:
                    countlvls += 1
                    row[f"title level {str(countlvls)}"] = ""

                writer.writerow(row)
                
    print("\n✅ All transcriptions prepared.\n")

###############################################################################################

# DEDUCE ALL IMAGES FROM FIRST AND LAST NAME

def span_2_list(filist, first, last):
    
    before = []
    actual_files = []
    after = []
    
    if "." in first:
        f = filist.index(".".join(first.split(".")[:-1]))
    else:
        f = filist.index(first)
    if "." in last:
        l = filist.index(".".join(last.split(".")[:-1]))
    else:
        l = filist.index(last)

    for file in filist:
        idx = filist.index(file)
        if idx >= f and idx <= l:
            actual_files.append(file)
        elif idx < f:
            before.append(file)
        else:
            after.append(file)
            
    return {'before' : before, 'actual files' : actual_files, 'after' : after}
                

################################################################################################
# ADD ARK & VIEW NUMBER TO IDENTIFIERS

def re_id(prefix, element):
    
    for idd in element.findall('.//*[@ID]'):
        elid = idd.get("ID")
        newid = f"doc_{prefix}_{elid}"
        del idd.attrib["ID"]
        idd.set("ID", newid)
        idd.set("{http://www.w3.org/XML/1998/namespace}id", newid)
    return element

################################################################################################
# GET TOKEN JSON FOR ONE PAGE

def tesstokens(layout, filename):
    # tesstokens(reidd, file)
    punctuation = "….,/:!'\"()[]"
    page = []
        
    for item in layout.findall('.//{http://www.loc.gov/standards/alto/ns-v3#}TextLine'):
        
        line_id = item.get('ID')
        
        for string in item.findall('./{http://www.loc.gov/standards/alto/ns-v3#}String'):
            
            str_id = string.get('ID')
            str_text = string.get('CONTENT')
            
            if str_text.endswith('-'):
                join = "yes"
            else:
                join = "no"
                
            if str_text[-1] in punctuation:
                punct = str_text[-1]
            else:
                punct = ""
            if len(str_text) > 2:
                if str_text[-2] == ".":
                    abbr = "yes"
                else:
                    abbr = "no"
            else:
                abbr = "no"
            
            page.append({
                'line' : line_id,
                'string' : str_id,
                'text' : str_text,
                'join' : join,
                'abbr' : abbr,
                'punct' : punct
            })
    
    return page

"""
def line_tokens(line, nsmap):
    
    if "===" in line["text"]:
        id_prov = [i for i in line["text ids"].split(" ")]
        ws = []
        ids = []
        count = 0
        for word in line["text"].split(" "):
            ids_local = []
            for item in word.split("==="):
                count += 1
                ids_local.append(ids[count])
            ws.append("".join(word.split("===")))
            ids.append(" ".join(ids_local))

    else:
        ws = [w for w in line["text"].split(" ")]
        ids = [i for i in line["text ids"].split(" ")]
    words = []
    
    for count, word in enumerate(ws):
        if word != "$$$":
            
            if word.startswith('#') == True and word.endswith('#') == True:
                w = et.Element("{http://www.tei-c.org/ns/1.0}w", nsmap=nsmap)
                w.set("{http://www.tei-c.org/ns/1.0}type", f"manual_transcription")
                w.text = ws[count]
                words.append(w)
                del w
                
            else:
                for actualw in word.split('///'):
                    w = et.Element("{http://www.tei-c.org/ns/1.0}w", nsmap=nsmap)
                    w.set("{http://www.tei-c.org/ns/1.0}corresp", f"#{ids[count]}")
                    w.text = actual_w
                    words.append(w)
                    del w
        
    return words

"""