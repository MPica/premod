# -*- coding: utf-8 -*-
# KW TO TABLE

import json, os, csv, xmltodict, itertools, sys, re
import lxml.etree as et
import numpy as np
import pandas as pd
from tqdm.notebook import tqdm


# NOTES
# 1. Parse the class files and gather the conditions.
# 2. Parse the TEI files.
#     - add <rs> entities as elements in the text,
#     - add an identifier to each <rs> element,
#     - declare the entities in the teiHeader,
#     - sketch the RDF in xenoData,
#     - update the metadata.
# 3. Parse again and draw a table per TEI file.