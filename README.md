# Premod pipeline for Modern auction catalogues

## About

This pipeline was defined by Morgane Pica, design engineer in Digital Humanities, for Camille Mestdagh's ANR project, "OBJECTive". It is meant to extract an organized database from digitized 19<sup>th</sup> c. art object auction sales. The current README file contains information necessary for a handover of the pipeline, and will probably change before the end of the project.

The main folders in this repository are `input` and `output`.

Before execution, the `input` should contain one folder per project and therefore a `input/OBJECTive` folder, with a few necessary files:
```shell
└── 📂 premod
	└── 📂 input
		└── 📂 OBJECTive
			├── 📄 iiif_manifests.txt
			┆
			├── 📂 classification
			┆	├── 📄 classification.json
			┆	├── 📄 ignore.csv
			┆	└── 📄 one-csv-per-destination-class.csv
			┆
			└── 📂 xml_input
				└── 📂 one-folder-per-work
					├── 📄 one-xml-per-transcribed-page.xml
					└── 📄 one-txt-per-transcribed-page.txt

```
For better understanding of the folder architecture produced by the script, here is also the commented `output` folder:
```shell
└── 📂 premod
	└──  📂 output
		└── 📂 one-folder-per-extraction-session
			┆	└── 📄 [The final tables will be included here.]
			┆
			└── 📂 one-folder-per-work
				┆
				├── 📂 metadata
				┆
				└── 📂 working_data
					├── 📂 ht_crisco
					┆	└── 📄 [This folder contains the intermediate files
					┆		produced by the NLP script.]
					├── 📂 raw
					┆	└── 📄 [This folder contains the ALTO transcriptions
					┆		produced by the script.]
					└── 📂 recap
						└── 📄 [This folder contains the intermediate files
							produced by the script.]

```
**Warning**: The name of the work folders should be included in the name of every file. Anything produced by the scripts will do it automatically, but for anything modified and/or added manually, please make sure of this.

Here are the libraries necessary to PreMod:

| Basics and quality-of-life | Specific formats | Data transformation |
| :---: | :---: | :---: |
| datetime<br/>time<br/>io<br/>sys<br/>os<br/>pathlib<br/>itertools<br/>tqdm | json<br/>csv<br/>lxml<br/>SPARQLWrapper | pytesseract<br/>re<br/>numpy<br/>pandas<br/>hopsparser<br/>xmltodict |

## Auction catalogues

If the catalogues are available through IIIF protocol (i.e. from Gallica), the file `input/OBJECTive/iiif_manifests.txt` should contain one IIIF manifest link per line. This file may be commented, as lines beginning by `#` will be ignored.

Using the script to download the images will allow you to make sure all files are named coherently.

The following code should then be executed:

```python
import os
from utils import A_navigation as nav
from utils import B_dl_iiif as dlpics

project = "OBJECTive"

# Make the output folder with a timestamp.
dir_date = nav.mk_tmsp_dir(os.getcwd(), project=project)

# Start the process.
dlpics.dlpics(iiif_list, dir_date)
```
The results may be found in `output/extraction_[dir_date]`.

## OCR with Pero OCR

This step will be using [Pero OCR](https://pero-ocr.fit.vutbr.cz), which gave excellent results on Modern printed documents. As of now, we are using the dedicated GUI.

We recommend:
* giving Pero OCR only relevant pages (remove images of the binding, etc.),
* giving Pero OCR at most 100 pages at a time, as the server may refuse to output documents too large,
* checking the documents before output, in order to remove useless lines (for instance, ".........." in a table of contents),
* downloading "all transcriptions", to get both TXT and XML (TXT is faster to check if need be, and we will be basing the rest of the pipeline on the XML).

The results should be included in the `input/OBJECTive/xml_input` folder, in one folder per work (for instance: `input/OBJECTive/xml_input/work1/work1_p0001.xml`).

## Layout typing following the DataCat pipeline

???

## TAL analysis with HT-CRISCO

## Database preparation with Getty AAT

## Reviewing the intermediate tables and adjusting the classification