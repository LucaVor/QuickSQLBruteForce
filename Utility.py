import pandas as pd

# Values must be a list of numerals
def sortKeyValuePair(keys, values):
    # Organize lists into a dictionary with keys as the keys and values as values
    pair = {}
    for i in range(0, len(keys)):
        pair[keys[i]] = values[i]

    # Return sorted keys derived from values
    keys = sorted(pair, key=pair.get)
    # Sort values
    values.sort()

    return keys, values

class GeneBase:
    def __init__(self, geneName, geneID):
        self.geneName = geneName
        self.geneID = geneID

def getSortedExcelArray(path):
    df = pd.read_csv(path)

    genes = []
    upDownMatching = {}

    for row in range(0, df.shape[0]):
        gene = df.at[row, df.columns[7]]

        if "nan" not in str(gene):
            thisGene = GeneBase(gene, df.at[row, df.columns[6]])
            genes.append(thisGene)
            upDownMatching[gene] = ("Up" if row == 0 else "Down")

    return genes, upDownMatching