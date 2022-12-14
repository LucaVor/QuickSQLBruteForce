from fpdf import FPDF

ALIGN_LEFT = 'L'
ALIGN_CENTER = 'C'

class PDFWriter(object):
    def __init__(self, localPath):
        self.pdf = FPDF() 
        
        self.LINE_HEIGHT = 5
        self.LINE_WIDTH = 200

        self.GRAPH_SIZE = 150

        self.localPath = localPath

        self.addPage()

    def addPage(self):
        self.pdf.add_page()

    def setFontSize(self, size):
        self.pdf.set_font("Arial", size = size)

    def multiLine(self, text, alignment):
        self.pdf.multi_cell(self.LINE_WIDTH, self.LINE_HEIGHT, txt = text, align = alignment)

    def writeLink(self, title, link):
        self.pdf.write(h = self.LINE_HEIGHT * 1.5, txt = title, link = link);

    def setLocalPath(self, path):
        self.localPath = path

    def writeImage(self, imagePath):
        self.pdf.image(imagePath, w=self.GRAPH_SIZE)

    def save(self):
        self.pdf.output(self.localPath)

