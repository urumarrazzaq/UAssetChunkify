import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QFileDialog, QListWidget, QMessageBox,
                             QTabWidget, QProgressBar, QLineEdit, QSpinBox, QGroupBox,
                             QCheckBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QIcon
from core import FileProcessor, CHUNK_SIZE

class WorkerThread(QThread):
    progress_updated = pyqtSignal(int)
    operation_completed = pyqtSignal(str, bool)
    
    def __init__(self, operation, *args, **kwargs):
        super().__init__()
        self.operation = operation
        self.args = args
        self.kwargs = kwargs
    
    def run(self):
        try:
            if self.operation == "split":
                file_path, chunk_size, delete_original, output_dir = self.args
                chunk_count = FileProcessor.split_file(file_path, chunk_size, delete_original, output_dir)
                self.operation_completed.emit(f"File split into {chunk_count} parts.", True)
            elif self.operation == "merge":
                output_path, chunk_paths, delete_chunks = self.args
                FileProcessor.merge_files(output_path, chunk_paths, delete_chunks)
                self.operation_completed.emit(f"Files merged successfully into {output_path}.", True)
            elif self.operation == "auto_split":
                directory, chunk_size, delete_original, output_dir = self.args
                large_files = FileProcessor.find_large_files(directory, chunk_size)
                for i, file in enumerate(large_files):
                    self.progress_updated.emit((i + 1) * 100 // len(large_files))
                    FileProcessor.split_file(os.path.join(directory, file), chunk_size, delete_original, output_dir)
                self.operation_completed.emit(f"Processed {len(large_files)} large files.", True)
            elif self.operation == "auto_merge":
                directory, delete_chunks, output_dir = self.args
                file_groups = FileProcessor.find_chunk_groups(directory)
                for i, (prefix, chunks) in enumerate(file_groups.items()):
                    self.progress_updated.emit((i + 1) * 100 // len(file_groups))
                    output_path = f"{prefix}{os.path.splitext(chunks[0])[1]}"
                    if output_dir:
                        output_path = os.path.join(output_dir, os.path.basename(output_path))
                    else:
                        output_path = os.path.join(directory, output_path)
                    FileProcessor.merge_files(
                        output_path, 
                        [os.path.join(directory, c) for c in chunks], 
                        delete_chunks
                    )
                self.operation_completed.emit(f"Merged {len(file_groups)} file groups.", True)
        except Exception as e:
            self.operation_completed.emit(f"Error: {str(e)}", False)

class FileSplitterUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chunkify")
        self.setGeometry(100, 100, 800, 600)
        self.setWindowIcon(QIcon.fromTheme("document-split"))
        
        # Central widget and main layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # Create tabs
        self.tabs = QTabWidget()
        self.main_layout.addWidget(self.tabs)
        
        # Add tabs
        self.create_split_tab()
        self.create_merge_tab()
        self.create_auto_tab()
        
        # Status bar
        self.status_bar = self.statusBar()
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(200)
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        # Set style
        self.set_style()
    
    def set_style(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QTabWidget::pane {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 10px;
                background: white;
            }
            QTabBar::tab {
                padding: 8px 16px;
                background: #e0e0e0;
                border: 1px solid #ccc;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background: white;
                border-bottom: 1px solid white;
                margin-bottom: -1px;
            }
            QGroupBox {
                border: 1px solid #ccc;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px;
            }
            QPushButton {
                padding: 6px 12px;
                background: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background: #45a049;
            }
            QPushButton:disabled {
                background: #cccccc;
            }
            QListWidget {
                border: 1px solid #ccc;
                border-radius: 4px;
                background: white;
            }
            QLineEdit, QSpinBox {
                padding: 6px;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
            QCheckBox {
                padding: 6px;
            }
        """)
        
        # Set font
        font = QFont()
        font.setPointSize(10)
        self.setFont(font)
    
    def create_split_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # File selection
        file_group = QGroupBox("File to Split")
        file_layout = QVBoxLayout(file_group)
        
        self.split_file_path = QLineEdit()
        self.split_file_path.setPlaceholderText("Select a file to split...")
        file_layout.addWidget(self.split_file_path)
        
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_split_file)
        file_layout.addWidget(browse_btn)
        
        # Output directory
        output_dir_group = QGroupBox("Output Directory")
        output_dir_layout = QVBoxLayout(output_dir_group)
        
        self.split_output_dir = QLineEdit()
        self.split_output_dir.setPlaceholderText("(Optional) Select output directory...")
        output_dir_layout.addWidget(self.split_output_dir)
        
        browse_output_btn = QPushButton("Browse...")
        browse_output_btn.clicked.connect(lambda: self.browse_output_directory(self.split_output_dir))
        output_dir_layout.addWidget(browse_output_btn)
        
        # Chunk size
        chunk_group = QGroupBox("Split Settings")
        chunk_layout = QVBoxLayout(chunk_group)
        
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("Chunk Size (MB):"))
        self.chunk_size = QSpinBox()
        self.chunk_size.setRange(1, 1000)
        self.chunk_size.setValue(CHUNK_SIZE // (1024 * 1024))
        size_layout.addWidget(self.chunk_size)
        size_layout.addStretch()
        chunk_layout.addLayout(size_layout)
        
        # Delete original checkbox
        self.delete_after_split = QCheckBox("Delete original file after splitting")
        chunk_layout.addWidget(self.delete_after_split)
        
        # Action button
        split_btn = QPushButton("Split File")
        split_btn.clicked.connect(self.start_split)
        
        layout.addWidget(file_group)
        layout.addWidget(output_dir_group)
        layout.addWidget(chunk_group)
        layout.addWidget(split_btn)
        layout.addStretch()
        
        self.tabs.addTab(tab, "Split File")
    
    def create_merge_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Output file
        output_group = QGroupBox("Output File")
        output_layout = QVBoxLayout(output_group)
        
        self.merge_output_path = QLineEdit()
        self.merge_output_path.setPlaceholderText("Enter output file name...")
        output_layout.addWidget(self.merge_output_path)
        
        # Output directory
        merge_output_dir_group = QGroupBox("Output Directory")
        merge_output_dir_layout = QVBoxLayout(merge_output_dir_group)
        
        self.merge_output_dir = QLineEdit()
        self.merge_output_dir.setPlaceholderText("(Optional) Select output directory...")
        merge_output_dir_layout.addWidget(self.merge_output_dir)
        
        browse_merge_output_btn = QPushButton("Browse...")
        browse_merge_output_btn.clicked.connect(lambda: self.browse_output_directory(self.merge_output_dir))
        merge_output_dir_layout.addWidget(browse_merge_output_btn)
        
        # Chunks list
        chunks_group = QGroupBox("Chunks to Merge")
        chunks_layout = QVBoxLayout(chunks_group)
        
        self.chunks_list = QListWidget()
        self.chunks_list.setSelectionMode(QListWidget.MultiSelection)
        chunks_layout.addWidget(self.chunks_list)
        
        add_chunks_btn = QPushButton("Add Chunks...")
        add_chunks_btn.clicked.connect(self.browse_chunks)
        chunks_layout.addWidget(add_chunks_btn)
        
        # Delete chunks checkbox
        self.delete_after_merge = QCheckBox("Delete chunk files after merging")
        chunks_layout.addWidget(self.delete_after_merge)
        
        # Action button
        merge_btn = QPushButton("Merge Files")
        merge_btn.clicked.connect(self.start_merge)
        
        layout.addWidget(output_group)
        layout.addWidget(merge_output_dir_group)
        layout.addWidget(chunks_group)
        layout.addWidget(merge_btn)
        layout.addStretch()
        
        self.tabs.addTab(tab, "Merge Files")
    
    def create_auto_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Directory selection
        dir_group = QGroupBox("Directory")
        dir_layout = QVBoxLayout(dir_group)
        
        self.auto_dir_path = QLineEdit()
        self.auto_dir_path.setPlaceholderText("Select a directory...")
        dir_layout.addWidget(self.auto_dir_path)
        
        browse_dir_btn = QPushButton("Browse...")
        browse_dir_btn.clicked.connect(self.browse_directory)
        dir_layout.addWidget(browse_dir_btn)
        
        # Output directory
        auto_output_dir_group = QGroupBox("Output Directory")
        auto_output_dir_layout = QVBoxLayout(auto_output_dir_group)
        
        self.auto_output_dir = QLineEdit()
        self.auto_output_dir.setPlaceholderText("(Optional) Select output directory...")
        auto_output_dir_layout.addWidget(self.auto_output_dir)
        
        browse_auto_output_btn = QPushButton("Browse...")
        browse_auto_output_btn.clicked.connect(lambda: self.browse_output_directory(self.auto_output_dir))
        auto_output_dir_layout.addWidget(browse_auto_output_btn)
        
        # Chunk size for auto-split
        auto_chunk_group = QGroupBox("Auto Split Settings")
        auto_chunk_layout = QVBoxLayout(auto_chunk_group)
        
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("Chunk Size (MB):"))
        self.auto_chunk_size = QSpinBox()
        self.auto_chunk_size.setRange(1, 1000)
        self.auto_chunk_size.setValue(CHUNK_SIZE // (1024 * 1024))
        size_layout.addWidget(self.auto_chunk_size)
        size_layout.addStretch()
        auto_chunk_layout.addLayout(size_layout)
        
        # Delete original checkbox
        self.auto_delete_after_split = QCheckBox("Delete original files after splitting")
        auto_chunk_layout.addWidget(self.auto_delete_after_split)
        
        # Delete chunks checkbox
        self.auto_delete_after_merge = QCheckBox("Delete chunk files after merging")
        auto_chunk_layout.addWidget(self.auto_delete_after_merge)
        
        # Action buttons
        auto_split_btn = QPushButton("Auto Split Large Files")
        auto_split_btn.clicked.connect(self.start_auto_split)
        
        auto_merge_btn = QPushButton("Auto Merge Chunks")
        auto_merge_btn.clicked.connect(self.start_auto_merge)
        
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(auto_split_btn)
        btn_layout.addWidget(auto_merge_btn)
        
        layout.addWidget(dir_group)
        layout.addWidget(auto_output_dir_group)
        layout.addWidget(auto_chunk_group)
        layout.addLayout(btn_layout)
        layout.addStretch()
        
        self.tabs.addTab(tab, "Auto Operations")
    
    def browse_split_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select File to Split")
        if file_path:
            self.split_file_path.setText(file_path)
    
    def browse_chunks(self):
        file_paths, _ = QFileDialog.getOpenFileNames(self, "Select Chunk Files")
        if file_paths:
            self.chunks_list.clear()
            for path in file_paths:
                self.chunks_list.addItem(path)
    
    def browse_directory(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Directory")
        if dir_path:
            self.auto_dir_path.setText(dir_path)
    
    def browse_output_directory(self, line_edit):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if dir_path:
            line_edit.setText(dir_path)
    
    def start_split(self):
        file_path = self.split_file_path.text()
        if not file_path:
            QMessageBox.warning(self, "Warning", "Please select a file to split.")
            return
        
        chunk_size = self.chunk_size.value() * 1024 * 1024
        delete_original = self.delete_after_split.isChecked()
        output_dir = self.split_output_dir.text() or None
        
        self.worker = WorkerThread("split", file_path, chunk_size, delete_original, output_dir)
        self.set_worker_connections(self.worker)
        self.worker.start()
        self.show_progress(True)
    
    def start_merge(self):
        output_path = self.merge_output_path.text()
        if not output_path:
            QMessageBox.warning(self, "Warning", "Please enter an output file name.")
            return
        
        chunk_paths = [self.chunks_list.item(i).text() for i in range(self.chunks_list.count())]
        if not chunk_paths:
            QMessageBox.warning(self, "Warning", "Please add at least one chunk file.")
            return
        
        # Handle output directory
        output_dir = self.merge_output_dir.text()
        if output_dir:
            output_filename = os.path.basename(output_path)
            output_path = os.path.join(output_dir, output_filename)
        else:
            output_dir = os.path.dirname(os.path.abspath(output_path)) if os.path.dirname(output_path) else os.getcwd()
            output_path = os.path.join(output_dir, os.path.basename(output_path))
        
        delete_chunks = self.delete_after_merge.isChecked()
        
        try:
            self.worker = WorkerThread("merge", output_path, chunk_paths, delete_chunks)
            self.set_worker_connections(self.worker)
            self.worker.start()
            self.show_progress(True)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to start merge: {str(e)}")
    
    def start_auto_split(self):
        dir_path = self.auto_dir_path.text()
        if not dir_path:
            QMessageBox.warning(self, "Warning", "Please select a directory.")
            return
        
        chunk_size = self.auto_chunk_size.value() * 1024 * 1024
        delete_original = self.auto_delete_after_split.isChecked()
        output_dir = self.auto_output_dir.text() or None
        
        self.worker = WorkerThread("auto_split", dir_path, chunk_size, delete_original, output_dir)
        self.set_worker_connections(self.worker)
        self.worker.start()
        self.show_progress(True)
    
    def start_auto_merge(self):
        dir_path = self.auto_dir_path.text()
        if not dir_path:
            QMessageBox.warning(self, "Warning", "Please select a directory.")
            return
        
        delete_chunks = self.auto_delete_after_merge.isChecked()
        output_dir = self.auto_output_dir.text() or None
        
        self.worker = WorkerThread("auto_merge", dir_path, delete_chunks, output_dir)
        self.set_worker_connections(self.worker)
        self.worker.start()
        self.show_progress(True)
    
    def set_worker_connections(self, worker):
        worker.progress_updated.connect(self.update_progress)
        worker.operation_completed.connect(self.operation_finished)
    
    def update_progress(self, value):
        self.progress_bar.setValue(value)
    
    def operation_finished(self, message, success):
        self.show_progress(False)
        if success:
            QMessageBox.information(self, "Success", message)
        else:
            QMessageBox.critical(self, "Error", message)
    
    def show_progress(self, show):
        self.progress_bar.setVisible(show)
        if show:
            self.progress_bar.setValue(0)