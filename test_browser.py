import sys
from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QApplication, QDesktopWidget, QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QLabel
from PyQt5.QtGui import QImageReader, QPixmap
import os


class ImageBrowser(QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        # Get the list of sub-folders
        subfolders = ['f1', 'f2']  # Replace with your actual sub-folders

        # Create main layout
        layout = QHBoxLayout(self)

        # Set fixed width as a fraction of the screen width
        screen_width = QDesktopWidget().screenGeometry().width()

        # Create list widget for sub-folders
        self.list_widget = QListWidget()
        self.list_widget.addItems(subfolders)
        self.list_widget.itemClicked.connect(self.on_folder_selected)

        list_widget_width = int(screen_width * 0.1)  # Adjust the fraction as needed
        self.list_widget.setFixedWidth(list_widget_width)  # Set fixed width for the list widget
        layout.addWidget(self.list_widget)

        # Create label to display image
        self.image_label = QLabel()
        layout.addWidget(self.image_label)
        image_label_width = int(screen_width * 0.8)  # Adjust the fraction as needed
        self.image_label.setFixedWidth(image_label_width)  # Set fixed width for the image label

        self.setLayout(layout)
        self.setWindowTitle('Image Browser')

    def on_folder_selected(self, item):
        # Get the selected sub-folder
        selected_folder = item.text()

        # Display the image from the selected sub-folder
        # image_path = f'./{selected_folder}/coupler.png'  # Replace with your actual image filename
        folder_path = os.path.join(os.getcwd(), selected_folder)  # Assuming the sub-folders are in the current working directory

        files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]

        # Filter for PNG files
        png_files = [f for f in files if f.lower().endswith('.png')]

        if not png_files:
            self.image_label.setText('No PNG image found in the selected folder')
            return

        # For simplicity, let's use the first PNG file found in the folder
        image_path = os.path.join(folder_path, png_files[0])

        self.display_image(image_path)

    def display_image(self, image_path):
        # Check if the image file exists
        if QImageReader(image_path).size() == QSize(0, 0):
            self.image_label.setText('Image not found')
            return

        # Display the image in the label
        pixmap = QPixmap(image_path)
        self.image_label.setPixmap(pixmap)
        self.image_label.setScaledContents(True)
        self.image_label.show()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    browser = ImageBrowser()
    browser.show()
    sys.exit(app.exec_())
