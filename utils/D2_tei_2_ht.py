# -*- coding: utf-8 -*-
# TEI TO HT

import json, os, itertools, re
import lxml.etree as et
from tqdm.notebook import tqdm
from hopsparser import parser
#from spellchecker import SpellChecker
from utils import A_navigation as nav

"""
NOTE
Most of these functions were copy-pasted and reworked from Rayan Ziane's
work on the High-Tech project at the Caen University (France), in 2022 and 2023.
As our file structures are different, it could not be made a module and,
therefore, the repositories are not linked. However, the full app
he developped for this project and its documentation may be
found here: https://github.com/RZiane/HT_CRISCO
"""

#####################################################################################

# def call_rzianes_ht_crisco(dir_date, lg_model, presto, corrtable, corrlanguage = "en"):
def call_rzianes_ht_crisco(tokenized, dir_date, lg_model, presto, corrtable):
    
    nsmap = {
        None: "http://www.tei-c.org/ns/1.0",
        "alto": "http://www.loc.gov/standards/alto/ns-v3#",
        "oai-pmh": "http://www.openarchives.org/OAI/2.0/",
        "dc": "http://purl.org/dc/elements/1.1/",
        "oai_dc": "http://www.openarchives.org/OAI/2.0/oai_dc/",
        "xml":"http://www.w3.org/XML/1998/namespace"
    }
    
    print("\n⏳ Now starting linguistical analysis.")
    
    
    file_dict = nav.parse_folders(dir_date)
    
    """
    def parse_folders(onedir, iiif = False):
    
        file_dict = {}

        for folder in os.listdir(onedir):
            path = f'{onedir}/{folder}'
            if Path(path).is_dir() == True and "checkpoint" not in folder:
                file_dict[path] = [f.name for f in os.scandir(f'{path}/working_data/raw') if f.is_file()]

        return file_dict
    """
    
    if tokenized == False:
        
        nav.mk_tmsp_dir(os.getcwd(), dir_date)
        
        
    else:
        
        for folder in tqdm(file_dict.keys()):

            ark = folder.split('/')[-1]
            print(f"\t☕ Now analyzing {ark}.")

            input_file = f'{folder}/working_data/recap/{ark}_tokenized_tei.xml'

            try:
                os.mkdir(f"{folder}/working_data/ht_crisco")
            except:
                print("ht_crisco folder already exists")
            output_file = f'{folder}/working_data/recap/{ark}_analyzed_tei.xml'
            for_hopsparser = f'{folder}/working_data/ht_crisco/{ark}_before.conllu'
            for_hops_json = f'{folder}/working_data/ht_crisco/{ark}_before.json'
            parsed = f'{folder}/working_data/ht_crisco/{ark}_after.conllu'
            syntaxed_xml = f'{folder}/working_data/ht_crisco/{ark}_conllu.xml'
            analyzed_xml = f'{folder}/working_data/recap/{ark}_conllu.xml'
            lemmed = f'{folder}/working_data/ht_crisco/{ark}_hops_and_ht.json'

            # This part of the pipeline is copied from
            # and refers to Rayan Ziane's work.
            # Because our file structure is different, much was
            # changed here.
            print("Conversion to CONLLU")
            conversion_xml2conllu(input_file, for_hopsparser, for_hops_json)
            print("HOPS parser")
            parser.parse(
                in_file = for_hopsparser,
                model_path = lg_model,
                out_file = parsed
            )

            print("Lemmatisation")
            lemmatized = process_lemmatisation(parsed, for_hopsparser, for_hops_json, corrtable, presto)
            #ortho_checked = check_nolem(lemmatized, corrlanguage)

            with open(lemmed, "w") as jsonfile:
                jsonfile.write(json.dumps(lemmatized, indent=4))

            # Write the final XML file to its location.
            nav.write_xml(synchronize_ht_tei(input_file, lemmatized, nsmap), output_file, "w")
            
    print("\t✅ All documents were analyzed.")
        
#####################################################################################

def tokenize4ht(orig):

# QUAND IL MANQUE QUELQUE CHOSE DANS LA STRUCTURATION
# À REFAIRE À PARTIR DU TRAVAIL SUR DEPUTEST EN COMMENTAIRE LÀ :
    
    """
        yippee = "/home/mpica/ownCloud/other-peoples-scripts/pierre-vernus_extraction-deputes/txt_a_analyser/xml/collection_3e_republique/working_data/recap/collection_3e_republique_orig.xml"

    nsmap = {
        None: "http://www.tei-c.org/ns/1.0",
        "xml":"http://www.w3.org/XML/1998/namespace"
    }

    new_root = et.Element("{http://www.tei-c.org/ns/1.0}text")

    with open(yippee) as xmlfile:
        root = et.fromstring(xmlfile.read())

    p_counter = 0
    s_counter = 0
    w_counter = 0

    for div in root.findall('.//{http://www.tei-c.org/ns/1.0}body/{http://www.tei-c.org/ns/1.0}div'):

        ident = div.get('{http://www.w3.org/XML/1998/namespace}id')
        print(ident)
        new_div = et.Element('{http://www.tei-c.org/ns/1.0}div')
        new_div.set('{http://www.w3.org/XML/1998/namespace}id', ident)

        for bio in div.findall('./{http://www.tei-c.org/ns/1.0}div'):

            new_bio = et.Element('{http://www.tei-c.org/ns/1.0}div')
            new_bio.set('{http://www.w3.org/XML/1998/namespace}id', f"{ident}_{bio.get('{http://www.tei-c.org/ns/1.0}type')}")

            new_bio.append(bio.find('./{http://www.tei-c.org/ns/1.0}head'))

            for s in bio.findall('.//{http://www.tei-c.org/ns/1.0}s'):
                s_counter += 1
                sid = f"{ident}_s_{s_counter}"
                s.set('{http://www.w3.org/XML/1998/namespace}id', sid)

                for w in s.findall('./{http://www.tei-c.org/ns/1.0}w'):

                    w_counter += 1
                    w.set('{http://www.tei-c.org/ns/1.0}n', str(w_counter))
                    w.set('{http://www.w3.org/XML/1998/namespace}id', f"s_{s_counter}_w_{w_counter}")

                w_counter = 0

            for p in bio.findall('.//{http://www.tei-c.org/ns/1.0}p'):
                p_counter += 1
                p.set('{http://www.w3.org/XML/1998/namespace}id', f"{ident}_p_{p_counter}")

                new_bio.append(p)

            new_div.append(new_bio)

        new_root.append(new_div)

    synchronized = et.tostring(new_root, xml_declaration=True, encoding="utf-8", pretty_print = False).decode('UTF-8')

    with open(yippee.replace('orig', 'tokenized_tei'), "w", encoding="utf-8") as xmlfile:
        xmlfile.write(synchronized)
    """

#####################################################################################

def check_nolem(dico, lg):
    
    spell = SpellChecker(language=lg)
    return_dict = {}
    
    for word in dico.keys():
        corr = {}
        
        if dico[word]['token_lemma'] == "_":
            
            try:
                corrected = spell.correction(dico[word]['token_word'])
                print(dico[word]['token_word'], corrected)
            except:
                corrected = dico[word]['token_word']
                print(dico[word]['token_word'], corrected)
        else:
            corrected = dico[word]['token_word']
        
        for wkey in dico[word].keys():
            if wkey == 'token_lemma':
                corr[wkey] = corrected
            else:
                corr[wkey] = dico[word][wkey]
                
        return_dict[word] = corr
    
    return return_dict

        
#####################################################################################


def synchronize_ht_tei(input_file, lemmatized, nsmap):
    
    with open(input_file) as xmlfile:
        tree = et.parse(xmlfile)
        root = tree.getroot()
        
        for token in root.findall('.//{http://www.tei-c.org/ns/1.0}w'):
            
            tokid = token.get('{http://www.w3.org/XML/1998/namespace}id')
            
            try:
                lemmd = lemmatized[tokid]
                
                token.set('{http://www.tei-c.org/ns/1.0}lemma', lemmd['token_lemma'])
                token.set('{http://www.tei-c.org/ns/1.0}pos', f'ud:{lemmd["token_ud"]} up:{lemmd["token_up"]}')
                token.set('head', lemmd['token_head'])
                token.set('{http://www.tei-c.org/ns/1.0}function', lemmd['token_function'])
                token.attrib.pop('n')
                token.set('n', lemmd['token_nb'])
            
            except Exception as e:
                print(e)
        
        return root
    
        
#####################################################################################

# FROM HT_CRISCO

def conversion_xml2conllu(inputfile, outputfile, recap):
    # On ouvre le fichier de sortie
    
    useless_tei = re.compile(r' xmlns:ns\d+="http://www.tei-c.org/ns/1.0"')
    useless_att = re.compile(r'ns\d+:')
    
    jsond = {}
    with open(outputfile, 'w', encoding="utf-8") as conll:

        # On importe le XML-TEI d'entrée et on le lit.
        with open(inputfile, encoding="utf-8") as xmlfile:
            tree = et.parse(xmlfile)
            root = tree.getroot()
            
            # Loops on top levels removed, as our documents have
            # different structure levels and we have @xml:id
            # values to identify our tokens with.

            for sentence in root.findall('.//{http://www.tei-c.org/ns/1.0}body//{http://www.tei-c.org/ns/1.0}s'):
                """
                # Token renumbering added by MPica
                s_count = 0
                for w in sentence.findall('./{http://www.tei-c.org/ns/1.0}w'):
                    s_count += 1
                    try:
                        del w.attrib['{http://www.tei-c.org/ns/1.0}n']
                        w.attrib['{http://www.tei-c.org/ns/1.0}n'] = str(s_count)
                    except:
                        if w.get('n') != None:
                            del w.attrib['n']
                        w.attrib['n'] = str(s_count)
                with open(inputfile.replace("_tokenized_tei", "_renumbered"), "w") as renum:
                    renum.write(useless_att.sub('', useless_tei.sub('', et.tostring(root, xml_declaration=True, encoding="utf-8", pretty_print = False).decode('UTF-8'))))
                """
                sentence_id = sentence.get('{http://www.w3.org/XML/1998/namespace}id')
                conll.write(f"\n\n# sent_id = {sentence_id}")
                
                jsond[sentence_id] = {}

                for word in sentence.findall('./{http://www.tei-c.org/ns/1.0}w'):

                    #On récupère les numéros de tokens
                    try:
                        word_nb = word.get('n')
                    except:
                        word_nb = word.get('{http://www.tei-c.org/ns/1.0}n')
                    
                    form = word.text

                    if word.findall("./*") is not None:
                        for child in word.findall("./{http://www.tei-c.org/ns/1.0}lb"):
                            form += child.tail

                    # Added by MPica
                    wmisc = word.get("{http://www.w3.org/XML/1998/namespace}id")

                    #dev print(form)
                    mot = str("\n"+word_nb+"\t"+form.replace("\t", "").replace("\n", "")+"\t_\t_\t_\t_\t_\t_\t_\t"+wmisc)
                    #On écrit le fichier de sortie
                    
                    jsond[sentence_id][word_nb] = {'form':form.replace("\t", "").replace("\n", ""), 'id':wmisc}

                    conll.write(mot)
    
    jsons = json.dumps(jsond, indent=4)
    with open(recap, "w") as jsonfile:
        jsonfile.write(jsons)

#####################################################################################

# FROM HT_CRISCO
# d_PRESTO = make_d_PRESTO(path_PRESTO)
# d_CorrTable = make_d_CorrTable(path_CorrTable)
                        
def process_lemmatisation(inputfile, before, recap, d_CorrTable, d_PRESTO):
    
    done_words = {}
    
    if type(inputfile) == str:
        words = conversion_conllu2dict(inputfile, before, recap)
    else:
        words = inputfile
    
    ids = list(words.keys())

    for w in tqdm(ids, total=len(ids)):

        token = words[w]
        token['no match in presto'] = []
        s_token = token['token_word'].lower().strip()
        s_udpos = token['token_ud']

        list_prpos = []
        list_prfeat = []
        list_lemma = []
        
        if s_token in d_PRESTO.keys():

            # résolution de l'ambiguité en comparant l'étiquette POS UD avec celle dans le dictionnaire PRESTO
            if len(d_PRESTO[s_token]) != 1: # si plusieurs valeurs pour une entrée dans le dictionnaire alors ambiguité
                for entry in d_PRESTO[s_token]: # itération des valeurs pour l'entrée
                    for tag in d_CorrTable[s_udpos]:
                        lemmatisation(entry, tag, list_prpos, list_prfeat, list_lemma)

            else:
                for tag in d_CorrTable[s_udpos]:
                    lemmatisation(d_PRESTO[s_token][0], tag, list_prpos, list_prfeat, list_lemma)

        # absence du verbe dans presto
        else:
            token['no match in presto'].append('Word')
            
        # RESULT n="1" lemma="_" pos="ud:NOUN up:_" head="0" function="root"

        list_lemma = list(sorted(set(list_lemma)))

        if list_lemma != []:

            if len(list_lemma) > 1:
                s_lemma = '///'.join(list_lemma)
            else:
                s_lemma = list_lemma[0]

            # Gestion de l'absence de conversion de l'étiquette UPenn
            try:
                token["token_lemma"] = s_lemma
            except NameError:
                s_lemma = '_'
                token["token_lemma"] = s_lemma

        elif list_lemma == [] and 'Word' not in token['no match in presto']:

            if s_udpos=='PROPN' or s_udpos=='PUNCT':
                s_lemma = token['token_word']
                token["token_lemma"] = s_lemma
            else:
                s_lemma = '_'
                token["token_lemma"] = s_lemma

                token['no match in presto'].append('POS')

        elif list_lemma == [] and 'Word' in token['no match in presto']:

            if s_udpos=='PROPN' or s_udpos=='PUNCT':
                s_lemma = s_token
                token['token_lemma'] = s_lemma
                token['no match in presto'].remove('Word')
            else:
                s_lemma = '_'
                token['token_lemma'] = s_lemma

        done_words[w] = token

    return done_words




def lemmatisation(entry, tag, list_prpos, list_prfeat, list_lemma):
    if entry[1] == tag[1]:
        if entry[1] in list_prpos:
            pass
        else:
            list_prpos.append(entry[1])

        if entry[2] in list_prfeat:
            pass
        else:
            list_prfeat.append(entry[2])

        for prfeat, prpos in zip(list_prfeat, itertools.cycle(list_prpos)):
            if entry[1] == prpos and entry[2] == prfeat:
                list_lemma.append(entry[3].lower())
        
#####################################################################################

# FROM HT_CRISCO
# Original function: conversion_conllu2xml()
                         
def conversion_conllu2dict(inputfile, before, recap):
    #on ouvre le fichier d'origine, et on construit une liste où chaque élément est une ligne du conll.
    corpus = []
    words = {}
    
    with_ids = {}
    with open(recap, encoding="utf-8") as jsonfile:
        jsonf = json.load(jsonfile)
        for s in jsonf.keys():
            with_ids[s] = jsonf[s]
    
    with open(inputfile, encoding='utf-8') as conll:
        for line in conll:
            corpus.append(line)

    #On parse le fichier conll en entrée, et on stocke les informations dans des variables
    currents = ""
    for line in corpus:
            
        #Si la ligne est un commentaire, il contient le X-PATH de la phrase. On récupère les infos.
            
        if line.startswith('#') == True:
            sid = line.split("=")[1].strip()
            currents = sid
            
        elif line.startswith('\n') == True:
            pass
            #Sinon, la ligne est un token. On récupère les informations de colonnes.
            
        else:
            
            info_token = line.split('\t')
            
            if with_ids[currents][info_token[0]]['form'] == info_token[1]:
                words[with_ids[currents][info_token[0]]['id']] = {
                    'token_nb' : info_token[0],
                    'token_word' : info_token[1],
                    'token_lemma' : info_token[2],
                    'token_ud' : info_token[3],
                    'token_up' : info_token[4],
                    'token_head' : info_token[6],
                    'token_function' : info_token[7]
                }
                
            else:
                print(f"\tThese two don't match: {with_ids[currents][token_nb]} & {token_word}")
            
    return words   

### Lemmatisation/Conversion tagsets ##########################
def make_d_PRESTO(path_PRESTO):
    
    #création du dictionnaire python à partir du dictionnaire PRESTO
    PRESTO = open(path_PRESTO, encoding='utf-8')

    #parsing du fichier .dff et création du dictionnaire python
    d_PRESTO = {}
    for entry in tqdm(PRESTO):
        entry = entry.rstrip("\n")
        entry = entry.split("/")
        if entry[0] in d_PRESTO:
            # nouvelle valeur si l'entrée est déjà dans le dictionnaire python
            d_PRESTO[entry[0]].append(entry)
        else:
            # nouvelle entrée dans le dictionnaire python
            d_PRESTO[entry[0]] = [entry]
            
    PRESTO.close()

    return d_PRESTO

def make_d_CorrTable(path_CorrTable):
    '''
    url = "https://unicloud.unicaen.fr/index.php/s/An5wqjdLHiPFwKt/download/dico_PRESTO_SIMPLE_10.01.23.dff"
    r = requests.get(url, allow_redirects=True)
    path_CorrTable = '/home/ziane212/crisco_work_ressources/test/corrTable.csv'
    open(path_CorrTable, 'wb').write(r.content)
    '''
    #création du dictionnaire python à partir de la table de conversion
    CorrTable = open(path_CorrTable, encoding='utf-8')
    d_CorrTable = {}
    for i in CorrTable:
        i = i.split(",")
        if i[4] in d_CorrTable:
            d_CorrTable[i[4]].append(i)
        else:
            d_CorrTable[i[4]]=[i]
            
    CorrTable.close()

    return d_CorrTable
                        
def preprocess_word_form(s_token):
    l_replace = [
        ('[', ''),
        ('(', ''), 
        (']', ''),
        (')', ''), 
        ('\t', ''),
        ('\n', ''), 
        ('"', ''),
        ('«', ''), 
        ('»', '')
    ]
        
    for r in l_replace:
        s_token = s_token.replace(*r)
    
    s_token = s_token.rstrip('-')

    if s_token.endswith('.') and len(s_token)!=1:
        s_token = s_token.replace('.', '')
    
    s_token = s_token.lower()

    return s_token