import sys
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtWidgets import QApplication, QDesktopWidget, QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QLabel, QPushButton
from PyQt5.QtGui import QImageReader, QPixmap
import os


class ImageBrowser(QWidget):
    def __init__(self, folder_path):
        super().__init__()

        self.folder_path = folder_path
        self.initUI()

    def initUI(self):
        # Get the list of sub-folders sorted by creation time
        subfolders = self.get_sorted_subfolders()

        # Create main layout
        layout = QHBoxLayout(self)

        # Create sub-layout for sub-folders list and refresh button
        sub_layout = QVBoxLayout()

        # Set fixed width as a fraction of the screen width
        screen_width = QDesktopWidget().screenGeometry().width()

        # Create refresh button
        refresh_button = QPushButton('Refresh')
        refresh_button.clicked.connect(self.refresh_subfolders)
        sub_layout.addWidget(refresh_button)

        # Create list widget for sub-folders
        self.list_widget = QListWidget()
        self.list_widget.addItems(subfolders)
        self.list_widget.itemClicked.connect(self.on_folder_selected)

        list_widget_width = int(screen_width * 0.1)  # Adjust the fraction as needed
        self.list_widget.setFixedWidth(list_widget_width)  # Set fixed width for the list widget
        sub_layout.addWidget(self.list_widget)

        # Add the sub-layout to the main layout
        layout.addLayout(sub_layout)

        # Create label to display image
        self.image_label = QLabel()
        layout.addWidget(self.image_label)
        image_label_width = int(screen_width * 0.8)  # Adjust the fraction as needed
        self.image_label.setFixedWidth(image_label_width)  # Set fixed width for the image label


        self.setLayout(layout)
        self.setWindowTitle('Image Browser')

    def refresh_subfolders(self):
        # Update the list of sub-folders and refresh the list widget
        self.subfolders = self.get_sorted_subfolders()
        self.list_widget.clear()
        self.list_widget.addItems(self.subfolders)

    def get_sorted_subfolders(self):
        # Get the list of sub-folders sorted by creation time
        return sorted(
            [d for d in os.listdir(self.folder_path) if os.path.isdir(os.path.join(self.folder_path, d))],
            key=lambda f: os.path.getctime(os.path.join(self.folder_path, f))
        )

    def on_folder_selected(self, item):
        # Get the selected sub-folder
        selected_folder = item.text()

        # Display the image from the selected sub-folder
        # image_path = f'./{selected_folder}/coupler.png'  # Replace with your actual image filename
        folder_path = os.path.join(os.getcwd(), self.folder_path, selected_folder)  # Assuming the sub-folders are in the current working directory

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

        # image_reader = QImageReader(image_path)

        # Display the image in the label
        image = QPixmap(image_path)

        # Get the dimensions of the image_label
        label_width = self.image_label.width()
        label_height = self.image_label.height()
        # self.image_label.setFixedSize(label_width, label_height)
        # self.image_label.setFixedSize(image_reader.size().width(), image_reader.size().height())


        # Scale the image while preserving aspect ratio
        scaled_image = image.scaled(
            label_width, label_height, transformMode=Qt.SmoothTransformation
            # label_width, label_height, aspectRatioMode=Qt.KeepAspectRatio, transformMode=Qt.SmoothTransformation
        )

        # Display the scaled image in the label
        self.image_label.setPixmap(scaled_image)

        self.image_label.setScaledContents(True)
        self.image_label.show()

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python script.py /path/to/subfolders")
        sys.exit(1)
    folder_path = sys.argv[1]

    app = QApplication(sys.argv)
    browser = ImageBrowser(folder_path)
    browser.show()
    sys.exit(app.exec_())
