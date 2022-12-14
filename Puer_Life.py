from selenium import webdriver
from selenium.webdriver.common.by import By
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image
import time
import numpy as np
from Utility import *
import threading
from ThreadingUtil import *
from math import floor

import pyodbc

table_name = "NCBI_Hashing"
database_name = "NCBI Lookup"

# Connect to SQL server
conn = pyodbc.connect('Driver={SQL Server};'
                        'Server=LAPTOP-JBAUAO59;'
                        f'Database={database_name};'
                        'Trusted_Connection=yes;')

cursor = conn.cursor()

cursor.execute(f"DELETE FROM {table_name}")
conn.commit()

def addToSQL(geneID, geneName, summary, alsoKnownAs, bibliography, bibliographyTitles, graphY):
    global conn, cursor, table_name, database_name

    converted_graph_y = ""
    if graphY != None:
        converted_graph_y = ",".join([str(x) for x in graphY])
    else:
        converted_graph_y = "None"
    converted_bibliograph = ",".join([str(x).replace("'","''") for x in bibliography])
    converted_bibliograph_titles = ";".join([str(x).replace("'","''") for x in bibliographyTitles])

    values = "'" + "','".join([str(x) for x in [geneID, geneName, summary.replace("'","''"), alsoKnownAs.replace("'","''"), converted_bibliograph, converted_bibliograph_titles, converted_graph_y]]) + "'"

    #print(f"INSERT INTO {table_name}(GeneID,GeneName,Summary,AlsoKnownAs,Bibliography,BibliographyTitles,GraphY) VALUES({values})")
    cursor.execute(f"INSERT INTO {table_name}(GeneID,GeneName,Summary,AlsoKnownAs,Bibliography,BibliographyTitles,GraphY) VALUES({values})")

# Premake labels for graph, always stay the same so...
labels = [
    "adrenal", "appendix", "bone marrow", "brain", "colon", 
    "duodenum", "endometrium", "esophagus", "fat", "gall bladder",
   "heart", "kidney", "liver", "lung", "lymph node", "ovary", "pancreas", 
   "placenta", "prostate", "salivary gland", "skin", "small intestine", 
   "spleen", "stomach", "testis", "thyroid", "urinary bladder"
]

def initializeDriver():
    options = webdriver.ChromeOptions()
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    driver = webdriver.Chrome(options=options)
    driver.maximize_window()
    return driver

def is_int_str(string):
    try:
        intify = float(string)
        return True, intify
    except:
        pass

    return False, -1

def deriveGeneInformation(driver, gene, geneID, sleepTime):
    global labels
    # Define base database URL and go to it

    # Detect if no gene was found
    if geneID == -1:
        return None, None, None, None, None, None

    # Use Gene ID to generate link for gene
    linkBaseURL = f"https://www.ncbi.nlm.nih.gov/gene/{geneID}"

    # Go to gene and sleep to give page time to load
    driver.get(linkBaseURL)
    # Unfortunate, but without this line, graph code won't work because graph wouldn't have loaded yet
    time.sleep(sleepTime)

    # Get all relavent HTML elements
    informationArray = driver.find_elements(By.TAG_NAME, "dd")
    rects = driver.find_elements(By.TAG_NAME, "rect")
    bibliographyElement = driver.find_element(By.CLASS_NAME, "generef-link")
    rawA = bibliographyElement.find_elements(By.TAG_NAME, "a")
    rawG = driver.find_elements(By.TAG_NAME, "g")

    # Instantiate empty bibliography lists
    bibliography = []
    bibliographyTitles = []

    # Brute force through all <a></a> tags
    for element in rawA:
        # Use arbitrary parameters to correctly isolate the <a> elements that contain bibliography element
        if "/pubmed/" in str(element.get_attribute("href")) and f"ncbi_uid={geneID}" in str(element.get_attribute("ref")):
            # Add information to lists
            bibliography.append(str(element.get_attribute("href")))
            bibliographyTitles.append(element.text)

    # Conveniently, the summary is always the ninth and alsoKnownAs is always the eighth element
    summary = informationArray[9].text
    alsoKnownAs = informationArray[8].text

    # Instantiate empty graph list (Will store Y values of each value on bar graph)
    graphY = []

    maxHeightValue = -100

    for i in range(0,len(rawG)):
        is_intable, height_val = is_int_str(rawG[i].text)

        if not is_intable:
            continue

        maxHeightValue = max(height_val, maxHeightValue)

    # Loop through all <rect></rect>
    for i in range(0,len(rects)):
        # Use arbitrary variable to isolate correct <rect> tags
        if "#336699" not in str(rects[i].get_attribute("fill")):
            continue

        # Divide the height attribute (The y of grpah) by coefficient to determine the correct value
        # matching both on my graph, and graph provided
        graphY.append((float(rects[i].get_attribute("height"))/347.2147106) * maxHeightValue)

    # Very occasionally the gene won't have a graph
    # So we return None for the graph
    if len(graphY) == 0:
        return geneID, summary, alsoKnownAs, bibliography, bibliographyTitles, None
    
    # Return all values
    return geneID, summary, alsoKnownAs, bibliography, bibliographyTitles, graphY

def renderGraph(sortedLabels, graphY, name):
    sortedLabels, _ = sortKeyValuePair([
            "adrenal", "appendix", "bone marrow", "brain", "colon", 
            "duodenum", "endometrium", "esophagus", "fat", "gall bladder",
            "heart", "kidney", "liver", "lung", "lymph node", "ovary", "pancreas", 
            "placenta", "prostate", "salivary gland", "skin", "small intestine", 
            "spleen", "stomach", "testis", "thyroid", "urinary bladder"
            ], graphY)

    fig = Figure(figsize=(12, 10), dpi=100)
    canvas = FigureCanvasAgg(fig)

    # Create axes subplot
    ax = fig.add_subplot(111)
    # Plot values
    ax.barh(sortedLabels, graphY)
    # Label axes
    ax.set_xlabel("RPKM")
    ax.set_ylabel("Samples")

    # Render canvas
    canvas.draw()
    # Extract canvas buffer for conversion to NUMPY array, convert that to a PIL image and save that
    # There is probably a better way to do it but it works
    buf = canvas.buffer_rgba()
    X = np.asarray(buf)
    im = Image.fromarray(X)

    im.save(name)
    
# Extract genes from excel
genes, upDownLabel = getSortedExcelArray(r"C:\Users\Luca Voros\source\repos\Puer Project\Puer Project\output.csv")

# Gene data scraped from threads
outputGeneData = []

totalDone = 0
started_at = time.time()

def executeWorker(workerID, start, end):
    global outputGeneData
    global genes, totalDone
    # Open selenium browser
    threadDriver = initializeDriver()

    # Iterator
    i = start

    # In order to skip gene
    continueOuterLoop = False
    
    # Loop through each gene
    for gene in genes[start:end]:   
        # How to to wait for page to load
        SLEEP_TIME = 6
        elevated_time = 7
        total_attempts = 0

        # Loop until the following code runs successfully
        # I do this because very occasionally, an error will be raised because when I run the time.sleep
        # its not enough to fully load the JS graph, and won't get proper values
        while True:
            # Break out of inner loop
            if continueOuterLoop:
                break

            try:
                # Extract Gene information
                geneID, summary, alsoKnownAs, bibliography, bibliographyTitles, graphY = deriveGeneInformation(threadDriver, gene.geneName, gene.geneID, SLEEP_TIME)

                # If there was an error finding gene
                if geneID == None and total_attempts > 4:
                    # Skip gene
                    continueOuterLoop = True
                    continue
                elif geneID == None:
                    total_attempts += 1
                    SLEEP_TIME = elevated_time
                    continue

                # If summary is empty, replace it
                if "provided by" not in summary:
                    summary = "No summary provided."

                    if total_attempts <= 4:
                        SLEEP_TIME = elevated_time
                        total_attempts += 1
                        continue

                # Set struct values
                data = GeneInformation(i, gene.geneName, geneID, summary, alsoKnownAs, graphY, bibliography, bibliographyTitles)

                # If no graph found
                if data.graphY == None and total_attempts <= 4:
                    # Retry once and increase sleep time
                    SLEEP_TIME = elevated_time
                    total_attempts += 1
                    # Raising exception to simply retry in the "try-catch" loop
                    raise Exception("")

                # Add to data
                outputGeneData.append(data)

                if data.graphY == None:
                    print("Failed to load graph.")

                break
            except Exception as err:
                if (str(err) != ""):
                    print(str(err))
                SLEEP_TIME = elevated_time
                pass

        # Skip this gene
        if continueOuterLoop:
            # Reset bool
            continueOuterLoop = False
            continue

        # Iterate
        i += 1
        totalDone += 1

        timeSince = time.time()-started_at
        timePer = timeSince/totalDone
        timeLeft = (len(genes) - totalDone) * timePer

        print(f"{round(timeLeft)}s left. Worker {workerID} finished {gene.geneName}. {len(genes)-len(outputGeneData)} more to go. %{round((len(outputGeneData)/len(genes)) * 100 * 1000) / 1000}")

# 4 Threads to split data into 4 chunks
WORKER_COUNT = 5

# How many genes each worker will accomplish
GENES_PER_WORKER = floor(len(genes) / WORKER_COUNT)

# Stores workers
workers = []
base = 0

for workerID in range(0, WORKER_COUNT):
    upperBound = base + GENES_PER_WORKER

    # Each worker will do genes[base:upperBound]
    
    if workerID == WORKER_COUNT-1:
        upperBound = len(genes)

    print (f"Worker {workerID}: {base}:{upperBound}")

    thread = threading.Thread(target = executeWorker, args=(workerID, base, upperBound))
    workers.append(thread)

    base = upperBound

# Start each thread
for worker in workers:
    worker.start()

# Make program wait for each thread to finish executing
for worker in workers:
    worker.join()

# Properly sort data
outputGeneData, _ = sortKeyValuePair(outputGeneData, [x.working_ID for x in outputGeneData])

# Write to PDF
i = 0
for gene in outputGeneData:
    print(f"Writing to SQL. %{round((i/len(outputGeneData)) * 100 * 1000) / 1000}")
    #geneID, geneName, summary, alsoKnownAs, bibliography, bibliographyTitles, graphY
    addToSQL (gene.geneID, gene.gene, gene.summary, gene.alsoKnownAs, gene.bibliography, gene.bibliographyTitles, gene.graphY)

    i += 1

conn.commit()