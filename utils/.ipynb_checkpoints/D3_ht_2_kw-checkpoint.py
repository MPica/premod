# -*- coding: utf-8 -*-
# HT TO KW

import json, os, csv, sys
import lxml.etree as et
import numpy as np
from tqdm.notebook import tqdm
from SPARQLWrapper import SPARQLWrapper, JSON

################################################################################################

# KEYWORD EXTRACTION AND COMPARISON

def kw_test(dir_date, project):
    
    nsmap = {
        "tei": "http://www.tei-c.org/ns/1.0",
        "alto": "http://www.loc.gov/standards/alto/ns-v3#",
        "oai-pmh": "http://www.openarchives.org/OAI/2.0/",
        "dc": "http://purl.org/dc/elements/1.1/",
        "oai_dc": "http://www.openarchives.org/OAI/2.0/oai_dc/",
        "xml":"http://www.w3.org/XML/1998/namespace"
    }
    
    transcriptions = [d for d in os.listdir(dir_date) if os.path.isdir(f"{dir_date}/{d}")]
    proj_kw = classified(f"{project}/classification")
    bypass_lemma = []
    ignore_lemma = []
    with open(f"{project}/{project.split('/')[-1]}_classification.json") as ign:
        ign_l = json.load(ign)
        for item in ign_l['ignore as syntactic root']:
            bypass_lemma.append(item)
        for item in ign_l['do not include in output']:
            ignore_lemma.append(item)
    
    
    print(f"\n⏳ Now starting keyword extraction.\n\nHere is the keyword typology I found in input/{project.split('/')[-1]}/classification :")
    for tp in proj_kw.keys():
        print("\t➣ "+tp.replace(".txt","").replace("-"," "))
    print("\nAccording to my instructions, I will be looking for alternative keywords when I encounter:")
    for ign in bypass_lemma:
        print("\t➣ " + ign)
    print("\nAccording to my instructions, I will not mark phrases whose root/keyword is:")
    for ign in ignore_lemma:
        print("\t➣ " + ign)
        
    all_kws = {}
    
    for folder in tqdm(transcriptions):
        ark = folder.split('/')[-1]
        print(f"\t☕ Now analyzing {ark}.")
        
        input_file = f'{dir_date}/{folder}/working_data/recap/{ark}_analyzed_tei.xml'
        got_kws, sentence_trees = get_kws(input_file, bypass_lemma, nsmap)
        
        for pos in got_kws.keys():
            dump_kws(dir_date, f"{folder}/working_data/recap", ark, got_kws[pos], f"lemmas_for_{pos}")
            
        nav.write_xml(sentence_trees, f'{dir_date}/{folder}/working_data/recap/{ark}_sentence_trees_tei.xml', "w")
        
        for pos in got_kws.keys():
            if pos in all_kws.keys():
                for kw in got_kws.keys():
                    if kw in all_kws[pos].keys():
                        for form in got_kws[pos][kw]:
                            if form not in all_kws[pos][kw]:
                                all_kws[pos][kw].append(form)
                    else:
                        all_kws[pos][kw] = [got_kws[pos][kw]]
            else:
                all_kws[pos] = [got_kws[pos]]
    
        for pos in all_kws.keys():
            dump_kws(dir_date, None, {dir_date.split('/')[-1]}, all_kws[pos], f"word_exploration_{pos}")
    
    no_cl = {}
    for kw in final_kws.keys():
        is_classed = False
        for cl in proj_kw.keys():
            for lm in proj_kw[cl]:
                if lm in kw or kw in lm:
                    is_classed = True
        if is_classed == False:
            no_cl[kw] = final_kws[kw]
    
    dump_kws(dir_date, None, {dir_date.split('/')[-1]}, no_cl, "preliminary_unclassified")
    
    # Pre-classify with Wikidata
    pre_classified = pre_class(no_cl)
    
    print("\n✅ Keyword extraction is done.")
        
################################################################################################

# MAKE A DICTIONARY TO STORE ALREADY CLASSIFIED KEYWORDS

def classified(proj_dir):
    
    ready_keywords = {}
    proj_classes = [f.name for f in os.scandir(proj_dir) if f.is_file()]
    
    for proj_class in proj_classes:
        class_file = f"{proj_dir}/{proj_class}"
        
        with open(class_file) as file:
            ready_keywords[proj_class] = [kw.strip().lower() for kw in file.readlines() if kw.strip() != ""]
        
    return ready_keywords

################################################################################################

# MAKE A CSV TABLE CONTAINING KEYWORD RESULTS

def dump_kws(dir_date, folder, prefix, kws, nm):
    
    if folder != None:
        path = f'{dir_date}/{folder}/{prefix}_{nm}.csv'
    else:
        path = f'{dir_date}/{prefix}_{nm}.csv'
        
    repath = path.replace('{','').replace('}','').replace("'","")

    with open(path, "w") as csvfile:
        fieldnames = ['lemma', 'forms in text']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for lemma in kws.keys():
            writer.writerow({'lemma': lemma, 'forms in text': '\r'.join(np.unique(kws[lemma]))})

################################################################################################

# GET AND ENCODE THE DEPENDENCIES OF A TOKEN AS NODES OF A TREE

def get_deps(sentence, token):
    
    num = token.get("n")
    head = token.get("head")
    form = w.text
    
    if token.find('./*') is not None:
        for c in token.findall('./*'):
            form += c.tail
    
    newtok = et.Element(
        token.get("function"),
        attrib={
            "form":form,
            "corresp": f'#{token.get("{http://www.w3.org/XML/1998/namespace}id")}',
            "pos": token.get("pos").split(" ")[0].replace("ud:",""),
            "lemma": token.get("lemma")
        })
    
    for dependance in sentence.findall(f"//{http://www.tei-c.org/ns/1.0}w[@head={num}]"):
        newtok.append(get_deps(sentence, dependance))
        
    return newtok

################################################################################################

# MAKE SENTENCES AS TREES

def sent_2_tree(sentence):
    
    corresp = f'#{sentence.get("{http://www.w3.org/XML/1998/namespace}id")}'
    
    tree = et.Element("syntTree")
    tree.set('corresp', corresp)
    root = sentence.xpath(".//{http://www.tei-c.org/ns/1.0}w[@function='root']")[0]
    deps = ".//{http://www.tei-c.org/ns/1.0}w[@head=" + root.get("n") + "]"

    for dependance in sentence.xpath(deps):
        tree.append(get_deps(sentence, root))
    
    return tree
            

################################################################################################

# DEDUCE THE KEYWORDS FROM SYNTACTIC DEPENDENCIES

def get_kws(xml, bypass, nsmap):
    
    teiHeader = xml.xpath('./{http://www.tei-c.org/ns/1.0}TEI/{http://www.tei-c.org/ns/1.0}teiHeader')
    trees = et.Element('synTrees')
    
    by_pos = {}
    
    with open(xml) as xmlfile:
        
        tree = et.parse(xmlfile)
        root = tree.getroot()
        
        for s in root.findall('.//{http://www.tei-c.org/ns/1.0}s'):
            
            # Make an actual XML syntactic tree.
            syntree = sent_2_tree(s)
            trees.append(syntree)
            
            by_pos = tree_digger(syntroot, bypass, by_pos)
    
    xeno = et.Element("{http://www.tei-c.org/ns/1.0}xenoData")
    xeno.append(trees)
    teiHeader.append(xeno)

    return by_pos, xml


################################################################################################

# DEEPER INTO THE TREE

def tree_digger(node, bypass, by_pos):
    
    fct_ignore = [
            "punct",
            "case",
            "cc",
            "det"
        ]
                
    info = dep.attrib # {'form':'', 'corresp':'', 'pos':'', 'lemma':''}
    lem = info['lemma']
    form = info['form']
    pos = info['pos']

    if form.lower() not in bypass and node.tag not in fct_ignore:
        
        if lem in by_pos[pos]:
            by_pos[pos][lem].append(form)
            print(f"\t\t{txt} ({lem}) was added to output dict.")

        elif form not in by_pos[pos][lem]:
            by_pos[pos][lem] = [txt]
            print(f"\t\t{txt} ({lem}) was added to output dict.")

    for dep in node.findall('./*'):
        tree_digger(node, bypass, kws, verbs)
        
    return kws, verbs


################################################################################################

# USE WIKIDATA TO PRECLASSIFY THE KEYWORDS WITHOUT CLASSES
# wdt:P31 (nature)
# Si c'est sur le Getty : https://vocab.getty.edu/
# https://vocab.getty.edu/resource/getty/search?q=soie&luceneIndex=Brief&indexDataset=AAT&_form=%2F

def pre_class(kws):
    
    endpoint_url = "https://query.wikidata.org/sparql"

    query_beg = """SELECT ?nature ?natureLabel WHERE {
      SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],mul,en". }
      ?nature wdt:P31 wd:Q28640.
    }
    LIMIT 100"""

    def get_results(endpoint_url, query):
        user_agent = "WDQS-example Python/%s.%s" % (sys.version_info[0], sys.version_info[1])
        # TODO adjust user agent; see https://w.wiki/CX6
        sparql = SPARQLWrapper(endpoint_url, agent=user_agent)
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        return sparql.query().convert()


    results = get_results(endpoint_url, query)

    for result in results["results"]["bindings"]:
        print(result)
