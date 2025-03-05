# -*- coding: utf-8 -*-

import json, os, csv
import lxml.etree as et
import numpy as np
from tqdm.notebook import tqdm
from utils import A_navigation as nav



################################################################################################
# CHAINED STRUCTURATION PROCESS :

def alto_to_struct(dir_date):
    
    nsmap = {
        None: "http://www.tei-c.org/ns/1.0",
        "alto": "http://www.loc.gov/standards/alto/ns-v3#",
        "oai-pmh": "http://www.openarchives.org/OAI/2.0/",
        "dc": "http://purl.org/dc/elements/1.1/",
        "oai_dc": "http://www.openarchives.org/OAI/2.0/oai_dc/",
        "xml":"http://www.w3.org/XML/1998/namespace"
    }
    
    print("\n⏳ Now compiling the information into TEI.")
    file_dict = nav.parse_folders(dir_date)
    
    for folder in tqdm(file_dict.keys()):
        ark = folder.split('/')[-1]
        print(ark)
        
        lvls = 0
        with open(f'{folder}/metadata/{ark}_instructions.csv') as csvfile:
            instructions = csv.DictReader(csvfile)
            lvls = int([row for row in instructions][0]["number of structuration levels"])
        
        with open(f'{folder}/working_data/recap/{ark}_full_alto.xml') as xmlfile:
            alto = et.parse(xmlfile).getroot()
        alto.set("{http://www.w3.org/XML/1998/namespace}id", f"doc_{ark}_alto_transcription")
        
        lines = []
        with open(f'{folder}/working_data/recap/{ark}_separate_lines.csv') as linefile:
            for line in csv.DictReader(linefile):
                lines.append(line)
        
        with open(f'{folder}/working_data/recap/{ark}_front_and_back.json') as jsonfile:
            front_back = json.load(jsonfile)
        
        with open(f"{folder}/metadata/{ark}_metadata.xml") as xmlfile:
            metadata = et.parse(xmlfile).getroot()
        oai_pmh = metadata.find("./{http://www.openarchives.org/OAI/2.0/}OAI-PMH")
        oai_pmh.set("{http://www.w3.org/XML/1998/namespace}id", f"doc_{ark}_original_md")
            
        with open(f"{folder}/metadata/{ark}_metadata.json") as jsonfile:
            iiif = json.load(jsonfile)["iiif"]
        
        TEIroot = et.Element("{http://www.tei-c.org/ns/1.0}TEI", nsmap=nsmap)
        
        xenos = [et.CDATA(json.dumps(iiif, ensure_ascii=False)), oai_pmh, alto]
        TEIroot.append(struct_md(ark, metadata, xenos, nsmap))
        
        TEIroot.append(struct_txt(lvls, ark, lines, front_back, nsmap))
        
        # Write XML file to its location.
        nav.write_xml(TEIroot, f'{folder}/working_data/recap/{ark}_tokenized_tei.xml', "w")


################################################################################################
# STRUCTURE METADATA

def struct_md(ark, metadata, xenos, nsmap):
    
    with open("utils/tei_template.xml") as xmlfile:
        tree = et.parse(xmlfile).getroot()
        
    teiHeader = tree.find('./{http://www.tei-c.org/ns/1.0}teiHeader')
    titS = teiHeader.find("./{http://www.tei-c.org/ns/1.0}fileDesc/{http://www.tei-c.org/ns/1.0}titleStmt")
    t = titS.find("./{http://www.tei-c.org/ns/1.0}title")
    try:
        t.text = "Semi-automatic transcription of : " + metadata.find("./iiif/Title").text
    except:
        try:
            t.text = "Semi-automatic transcription of : " + metadata.find(".//{http://purl.org/dc/elements/1.1/}title").text
        except:
            print(f"\tI cannot find a title for this source, you will need to add it manually.")
    
    for author in metadata.findall(".//{http://purl.org/dc/elements/1.1/}author"):
        a = et.Element("{http://www.tei-c.org/ns/1.0}author", nsmap=nsmap)
        a.text = author.text
        titS.append(a)
        del a
    
    for author in metadata.findall("./iiif/Author"):
        a = et.Element("{http://www.tei-c.org/ns/1.0}author", nsmap=nsmap)
        a.text = author.text
        titS.append(a)
        del a
    
    source = teiHeader.find(".//{http://www.tei-c.org/ns/1.0}bibl")
    
    jsonid = f"doc_{ark}_iiif_mds"
    md_list = [f"#{jsonid}", f"#doc_{ark}_alto_transcription", f"#doc_{ark}_original_md"]
    if metadata.find("./iiif/Source_Images") is not None:
        md_list.append(metadata.find("./iiif/Source_Images").text)
    if metadata.find(".//{http://purl.org/dc/elements/1.1/}identifier") is not None:
        for dcid in metadata.findall(".//{http://purl.org/dc/elements/1.1/}identifier"):
            md_list.append(dcid.text)
    source.set("{http://www.tei-c.org/ns/1.0}corresp", " ".join(np.unique(md_list)))
    
    xenojson = et.Element("{http://www.tei-c.org/ns/1.0}xenoData", nsmap=nsmap)
    xenojson.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    xenojson.set("{http://www.w3.org/XML/1998/namespace}id", jsonid)
    xenojson.text = xenos[0]
    teiHeader.append(xenojson)
    
    for el in xenos[1:]:
        otherxeno = et.Element("{http://www.tei-c.org/ns/1.0}xenoData")
        otherxeno.append(el)
        teiHeader.append(otherxeno)
        del otherxeno
        
    return teiHeader

################################################################################################
# STRUCTURE THE TEXT ELEMENT

def struct_txt(lvls, ark, lines, front_back, nsmap):
    
    text = et.Element("{http://www.tei-c.org/ns/1.0}text", nsmap=nsmap)
    front = et.SubElement(text, "{http://www.tei-c.org/ns/1.0}front", nsmap=nsmap)
    front.set("{http://www.w3.org/XML/1998/namespace}id", f"doc_{ark}_front")
    frontp = et.SubElement(front, "{http://www.tei-c.org/ns/1.0}p", nsmap=nsmap)
    
    for line in front_back["front"].keys():
        frl = et.Element("{http://www.tei-c.org/ns/1.0}lb", nsmap=nsmap)
        frl.set("{http://www.tei-c.org/ns/1.0}corresp", f"#{line}")
        frl.tail = " ".join(front_back["front"][line]["tokens"])
        frontp.append(frl)
        del(frl)
    
    body = struct_body(lvls, ark, lines, nsmap)
    sentenced = with_sentences(ark, body, nsmap)
    ided = with_ids(sentenced, f"doc_{ark}")
    
    text.append(ided)
        
    back = et.SubElement(text, "{http://www.tei-c.org/ns/1.0}back", nsmap=nsmap)
    back.set("{http://www.w3.org/XML/1998/namespace}id", f"doc_{ark}_back")
    backp = et.SubElement(back, "{http://www.tei-c.org/ns/1.0}p", nsmap=nsmap)
    
    for line in front_back["back"].keys():
        bl = et.Element("{http://www.tei-c.org/ns/1.0}lb", nsmap=nsmap)
        bl.set("{http://www.tei-c.org/ns/1.0}corresp", f"#{line}")
        bl.tail = " ".join(front_back["back"][line]["tokens"])
        backp.append(bl)
        del bl
    
    return text

################################################################################################
# STRUCTURE THE BODY OF THE TEXT
        
def struct_body(lvls, ark, lines, nsmap):
    
    commons = ["paragraph beginning", "text", "page", "line id", "text ids"]
    body = et.Element("{http://www.tei-c.org/ns/1.0}body", nsmap=nsmap)
    body.set("{http://www.w3.org/XML/1998/namespace}id", f"doc_{ark}_body")
    
    redone = redo_lines(lines)
    folded = fold_ps(lvls, redone)
    
    for div in make_divs(folded, nsmap):
        body.append(div)
    
    return body


################################################################################################
# ADD SENTENCE ELEMENTS
        
def with_sentences(file, text, nsmap):
    
    s_count = 0
    w_count = 0
    p_count = 0
    
    for el in text.findall(".//*[{http://www.tei-c.org/ns/1.0}w]"):
        
        parags = []
        s = et.Element("{http://www.tei-c.org/ns/1.0}s", nsmap=nsmap)
        empty = True
        
        for w in el.findall("./{http://www.tei-c.org/ns/1.0}w"):
            if w.text != ".":
                s.append(w)
                empty = False
            else:
                s.append(w)
                parags.append(s)
                del s
                s = et.Element("{http://www.tei-c.org/ns/1.0}s", nsmap=nsmap)
                empty = True
        
        if empty == False:
            parags.append(s)
            
        el.clear()
        for s in parags:
            el.append(s)
    
            
    for count, p in enumerate(text.findall(".//{http://www.tei-c.org/ns/1.0}p")):
        p_count += 1
        p.set("{http://www.w3.org/XML/1998/namespace}id", f"doc_{file}_p_{str(p_count)}")
        
    for w in text.findall(".//{http://www.tei-c.org/ns/1.0}w"):
        w_count += 1
        w.set("{http://www.w3.org/XML/1998/namespace}id", f"doc_{file}_w_{str(w_count)}")
        
    for s in text.findall(".//{http://www.tei-c.org/ns/1.0}s"):
        s_count += 1
        s_tokens = 0
        
        s.set("{http://www.w3.org/XML/1998/namespace}id", f"doc_{file}_s_{str(s_count)}")
        
        for w in s.findall(".//{http://www.tei-c.org/ns/1.0}w"):
            s_tokens += 1
            w.set("{http://www.tei-c.org/ns/1.0}n", str(s_tokens))
        
    return text
                
                
        
def with_ids(element, current):
        
    if element.findall("./{http://www.tei-c.org/ns/1.0}div") is not None:
        
        for count, div in enumerate(element.findall("./{http://www.tei-c.org/ns/1.0}div"), 1):
            divid = f"{current}_{str(format(count, '03d'))}"
            div.set("{http://www.w3.org/XML/1998/namespace}id", divid)
            
            if div.find('./{http://www.tei-c.org/ns/1.0}head') is not None:
                div.find('./{http://www.tei-c.org/ns/1.0}head').set("{http://www.w3.org/XML/1998/namespace}id", divid + "_head")
            
            div = with_ids(div, divid)
            
    return element

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


def redo_lines(lines):
    
    redone = []
    by_ps = []
    commons = ["text", "page", "line id", "text ids"]
    p_count = 0
    was_title = False
    title = ["", []]
    this_p = ["", []]
    
    for line in lines:
        new = {}
        nature = ""
        for column in line.keys():
            if column in commons:
                new[column] = line[column]
            elif "title level" in column or column == "paragraph beginning":
                if "x" in line[column].lower():
                    nature = column
            else:
                print(f"NEVER HEARD OF SUCH A COLUMN: {column}")
            
            if len(nature) == 0:
                new["nature"] = "basic"
            else:
                new["nature"] = nature
                
        if new["nature"] == "basic":
            new["which p"] = f"paragraph nb {str(p_count)}"
        elif new["nature"] == "paragraph beginning":
            p_count += 1
            new["which p"] = f"paragraph nb {str(p_count)}"          

        redone.append(new)
    
    for line in redone:
        
        if line["nature"] == "basic":
            this_p[1].append(line)
        
        elif line["nature"] == "paragraph beginning":
            
            if was_title == True:
                by_ps.append(title)
                was_title = False
            elif len(this_p[1]) != 0:
                by_ps.append(this_p)
            this_p = [line["which p"], [line]]
            
            
        else:
            if was_title == True:
                if line["nature"] == title[0]:
                    title[1].append(line)
                else:
                    by_ps.append(title)
                    title = [line["nature"], [line]]
            else:
                title = [line["nature"], [line]]
                if len(this_p[1]) != 0:
                    by_ps.append(this_p)
                    this_p = ["", []]
            
            was_title = True
            
    by_ps.append(this_p)
    
    return by_ps

def fold_ps(lvl, ps):
    
    max_lvl = "title level " + str(lvl)
    folded = []
    current = [f"div level {str(lvl)}", []]
    
    for p in ps:
        if "paragraph nb" in p[0] or "div level" in p[0]:
            current[1].append(p)
        elif p[0] == max_lvl:
            if len(current[1]) != 0:
                folded.append(current)
                current = [f"div level {lvl}", []]
            current[1].append(p)
        else:
            folded.append(p)
    
    folded.append(current)
    
    if lvl-1 != 0:
        refolded = fold_ps(lvl-1, folded)
    else:
        refolded = folded
        
    return refolded

def make_divs(folded, nsmap):
    
    current = []
    
    for item in folded:
        if "div level" in item[0]:
            subdiv = et.Element("{http://www.tei-c.org/ns/1.0}div", nsmap=nsmap)
            for sub in make_divs(item[1], nsmap):
                subdiv.append(sub)
            current.append(subdiv)
        elif "title level" in item[0]:
            tit = et.Element("{http://www.tei-c.org/ns/1.0}head", nsmap=nsmap)
            for wlb in p_tokens(item[1], nsmap):
                tit.append(wlb)
            current.append(tit)
        elif "paragraph nb" in item[0]:
            p = et.Element("{http://www.tei-c.org/ns/1.0}p", nsmap=nsmap)
            for wlb in p_tokens(item[1], nsmap):
                p.append(wlb)
            current.append(p)
    
    return current

    
def p_tokens(current, nsmap):
    
    parag = []
    was_cut = False
    end_text = ""
    end_corresp = ""
    
    for line in current:
        txt = line["text"].split(" ")
        ids = line["text ids"].split(" ")
        
        if was_cut == True:
            end_token = et.Element("{http://www.tei-c.org/ns/1.0}w", attrib={"{http://www.tei-c.org/ns/1.0}corresp" : f"#{end_corresp} #{ids[0]}"}, nsmap=nsmap)
            end_token.text = end_text
            lb = et.Element("{http://www.tei-c.org/ns/1.0}lb", attrib={"{http://www.tei-c.org/ns/1.0}corresp" : f"#{line['line id']}", "{http://www.tei-c.org/ns/1.0}break": "no"}, nsmap=nsmap)
            
            parts = de_punct(txt[0])
            lb.tail = parts[0]
            end_token.append(lb)
            parag.append(end_token)
            
            for part in parts[1:]:
                w = et.Element("{http://www.tei-c.org/ns/1.0}w", attrib={"{http://www.tei-c.org/ns/1.0}corresp":f"#{ids[0]}"}, nsmap=nsmap)
                w.text = part
                parag.append(w)
                del w
            
            del txt[0]
            del ids[0]
        else:
            linebeg = et.Element("{http://www.tei-c.org/ns/1.0}lb", attrib={"{http://www.tei-c.org/ns/1.0}corresp": f"#{line['line id']}"}, nsmap=nsmap)
            linebeg.set("{http://www.tei-c.org/ns/1.0}corresp",f"#{line['line id']}")
            parag.append(linebeg)
            del linebeg
        
        if len(txt) == 0:
            was_cut = False
            
        else:
            
            if txt[-1].endswith("-") == True:
                was_cut = True
                
                chars = [char for char in txt[-1]]
                nodash = "".join(chars[:-1])
                
                parts = de_punct(nodash)
                end_text = parts[-1]
                end_corresp = ids[-1]
                del txt[-1]
                del ids[-1]
                
                for part in parts[:-1]:
                    txt.append(part)
                    ids.append(end_corresp)
                
            else:
                was_cut = False

            for count, word in enumerate(txt, 0):
                
                for part in de_punct(word):
                    w = et.Element("{http://www.tei-c.org/ns/1.0}w", attrib={"{http://www.tei-c.org/ns/1.0}corresp":f"#{ids[count]}"}, nsmap=nsmap)
                    w.text = part
                    parag.append(w)
                    del w
    return parag



def de_punct(word):
    
    punctuated = ".,;:!?'՚ʼߴ＇’”\"‘“ˮ-—"
    spaced = ""
    
    for sign in word:
        if sign in punctuated:
            spaced +=  f" {sign} "
        else:
            spaced += sign
    
    final = spaced.strip()
    
    return [w for w in final.split(" ")]