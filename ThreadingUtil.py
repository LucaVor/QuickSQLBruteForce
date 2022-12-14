# Struct containing gene information
class GeneInformation:
    def __init__(self, workingID, gene, geneID, summary, alsoKnownAs, graphY, bibliography, bibliographyTitles):
        self.gene = gene
        self.geneID = geneID
        self.summary = summary
        self.alsoKnownAs = alsoKnownAs
        self.graphY = graphY
        self.bibliography = bibliography
        self.bibliographyTitles = bibliographyTitles
        self.working_ID = workingID