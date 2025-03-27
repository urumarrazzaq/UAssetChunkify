import sys
from PyQt5.QtWidgets import QApplication
from ui import FileSplitterUI

def main():
    app = QApplication(sys.argv)
    
    # Set application metadata
    app.setApplicationName("UAssetChunkify")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("Umar Razzaq")
    
    window = FileSplitterUI()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()