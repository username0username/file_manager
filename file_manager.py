import sys
import os
import shutil
from PySide6.QtWidgets import QApplication, QMainWindow, QTreeView, QVBoxLayout, QWidget, QFileSystemModel, QLineEdit, QPushButton, QHBoxLayout, QMessageBox, QInputDialog, QMenu, QHeaderView
from PySide6.QtCore import QDir, Qt, QFileInfo, QSize

class FileListApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Файловый менеджер")
        self.setGeometry(100, 100, 800, 600)

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.create_widgets()

    def create_widgets(self):
        self.layout = QVBoxLayout()

        self.create_path_widgets()
        self.create_tree_view()

        self.central_widget.setLayout(self.layout)

    def create_path_widgets(self):
        self.path_layout = QHBoxLayout()

        self.back_button = self.create_button("Назад", self.go_back)
        self.path_layout.addWidget(self.back_button)

        self.path_edit = QLineEdit(self)
        self.path_layout.addWidget(self.path_edit)

        self.open_button = self.create_button("Открыть", self.open_folder_from_text)
        self.path_layout.addWidget(self.open_button)

        self.layout.addLayout(self.path_layout)

    def create_tree_view(self):
        self.tree_view = QTreeView(self)
        self.model = QFileSystemModel()
        self.model.setRootPath("")
        self.tree_view.setModel(self.model)
        self.tree_view.setHeaderHidden(False)
        self.tree_view.setSortingEnabled(True)
        self.tree_view.setRootIndex(self.model.index(""))
        self.tree_view.doubleClicked.connect(self.handle_double_click)
        self.tree_view.setRootIsDecorated(False)
        self.tree_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_view.customContextMenuRequested.connect(self.show_context_menu)

        header = self.tree_view.header()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionsClickable(True)
        header.sectionClicked.connect(self.on_header_clicked)

        self.layout.addWidget(self.tree_view)

        self.sort_column = 0
        self.sort_order = Qt.AscendingOrder

    def create_button(self, text, on_click):
        button = QPushButton(text, self)
        button.clicked.connect(on_click)
        return button

    def handle_double_click(self, index):
        if self.model.isDir(index):
            folder_path = self.model.filePath(index)
            self.tree_view.setRootIndex(index)
            self.path_edit.setText(folder_path)
            self.update_create_folder_button_state()
        else:
            file_path = self.model.filePath(index)
            try:
                os.startfile(file_path)  # для Windows
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", f"Не удалось открыть файл {file_path}.\nОшибка: {str(e)}")

    def on_header_clicked(self, logical_index):
        if self.sort_column == logical_index:
            self.sort_order = Qt.DescendingOrder if self.sort_order == Qt.AscendingOrder else Qt.AscendingOrder
        else:
            self.sort_column = logical_index
            self.sort_order = Qt.AscendingOrder

        self.tree_view.sortByColumn(self.sort_column, self.sort_order)

    def go_back(self):
        current_index = self.tree_view.rootIndex()
        parent_index = self.model.parent(current_index)
        if parent_index.isValid():
            folder_path = self.model.filePath(parent_index)
            self.tree_view.setRootIndex(parent_index)
            self.path_edit.setText(folder_path)
            self.update_create_folder_button_state()
        else:
            self.path_edit.clear()
            self.display_drives()

    def open_folder_from_text(self):
        folder_path = self.path_edit.text()
        dir_check = QDir(folder_path)
        if dir_check.exists():
            self.model.setRootPath(folder_path)
            self.model.revert()
            self.tree_view.setRootIndex(self.model.index(folder_path))
            self.update_create_folder_button_state()
        else:
            QMessageBox.warning(self, "Ошибка", f"Директория не найдена: {folder_path}")

    def display_drives(self):
        self.model.setRootPath("")
        self.model.revert()
        self.tree_view.setRootIndex(self.model.index(""))
        self.update_create_folder_button_state()

    def update_create_folder_button_state(self):
        is_root = self.tree_view.rootIndex().data() == ""
        self.open_button.setEnabled(not is_root)

    def copy_item(self, index):
        self.copied_item_path = self.model.filePath(index)

    def paste_item(self):
        if hasattr(self, 'copied_item_path') and self.copied_item_path:
            destination_folder = self.path_edit.text()
            destination_path = os.path.join(destination_folder, os.path.basename(self.copied_item_path))
            if not QFileInfo(destination_path).exists():
                try:
                    if os.path.isdir(self.copied_item_path):
                        shutil.copytree(self.copied_item_path, destination_path)
                    else:
                        shutil.copy2(self.copied_item_path, destination_path)
                    self.model.revert()
                    self.tree_view.setRootIndex(self.model.index(destination_folder))
                    self.copied_item_path = None
                except Exception as e:
                    QMessageBox.warning(self, "Ошибка", f"Ошибка при вставке файла: {str(e)}")
            else:
                QMessageBox.warning(self, "Ошибка", "Элемент с таким именем уже существует.")
        else:
            QMessageBox.warning(self, "Ошибка", "Сначала скопируйте файл.")

    def show_context_menu(self, position):
        index = self.tree_view.indexAt(position)
        menu = QMenu(self)

        if index.isValid():
            if self.model.isDir(index):
                menu.addAction("Открыть", lambda: self.handle_double_click(index))
                menu.addAction("Удалить", lambda: self.delete_item(index))
                menu.addAction("Копировать", lambda: self.copy_item(index))
                menu.addAction("Переименовать", lambda: self.rename_item(index))
            else:
                menu.addAction("Открыть", lambda: self.handle_double_click(index))
                menu.addAction("Удалить", lambda: self.delete_item(index))
                menu.addAction("Копировать", lambda: self.copy_item(index))
                menu.addAction("Переименовать", lambda: self.rename_item(index))
        else:
            create_folder_action = menu.addAction("Создать папку")
            create_file_action = menu.addAction("Создать файл")
            paste_item_action = menu.addAction("Вставить файл")

            create_folder_action.triggered.connect(self.create_folder)
            create_file_action.triggered.connect(self.create_file)
            paste_item_action.triggered.connect(self.paste_item)

        menu.exec(self.tree_view.mapToGlobal(position))

    def rename_item(self, index):
        old_name = self.model.fileName(index)
        new_name, ok = QInputDialog.getText(self, "Переименовать", "Новое имя:", QLineEdit.Normal, old_name)
        if ok and new_name:
            new_name = new_name.strip()
            if new_name != old_name:
                current_path = self.path_edit.text()
                old_path = self.model.filePath(index)
                new_path = os.path.join(current_path, new_name)

                if not QFileInfo(new_path).exists():
                    try:
                        os.rename(old_path, new_path)
                        self.model.setData(index, new_name, Qt.EditRole)
                        self.model.revert()
                        self.tree_view.setRootIndex(self.model.index(current_path))
                    except Exception as e:
                        QMessageBox.warning(self, "Ошибка", f"Ошибка при переименовании файла: {str(e)}")
                else:
                    QMessageBox.warning(self, "Ошибка", "Элемент с таким именем уже существует.")
            else:
                QMessageBox.warning(self, "Ошибка", "Введите новое имя для переименования.")

    def create_folder(self):
        folder_name, ok = QInputDialog.getText(self, "Создать папку", "Имя папки:")
        if ok:
            folder_name = folder_name.strip()
            if folder_name:
                current_path = self.path_edit.text()
                new_folder_path = os.path.join(current_path, folder_name)
                if not os.path.exists(new_folder_path):
                    try:
                        os.makedirs(new_folder_path)
                        self.model.revert()
                        self.tree_view.setRootIndex(self.model.index(current_path))
                        self.update_create_folder_button_state()
                    except Exception as e:
                        QMessageBox.warning(self, "Ошибка", f"Ошибка при создании папки: {str(e)}")
                else:
                    QMessageBox.warning(self, "Ошибка", "Папка уже существует.")
            else:
                QMessageBox.warning(self, "Ошибка", "Введите имя папки.")

    def create_file(self):
        file_name, ok = QInputDialog.getText(self, "Создать файл", "Имя файла:")
        if ok:
            file_name = file_name.strip()
            if file_name:
                current_path = self.path_edit.text()
                file_path = os.path.join(current_path, file_name)
                if '.' in file_name:
                    try:
                        if not os.path.exists(file_path):
                            with open(file_path, 'w') as file:
                                pass
                            self.model.revert()
                            self.tree_view.setRootIndex(self.model.index(current_path))
                        else:
                            QMessageBox.warning(self, "Ошибка", "Файл уже существует.")
                    except Exception as e:
                        QMessageBox.warning(self, "Ошибка", f"Ошибка при создании файла: {str(e)}")
                else:
                    QMessageBox.warning(self, "Ошибка", "Введите имя файла с расширением.")
            else:
                QMessageBox.warning(self, "Ошибка", "Введите корректное имя файла.")

    def delete_item(self, index):
        item_path = self.model.filePath(index)
        confirm = QMessageBox.question(self, "Подтверждение удаления", f"Вы уверены, что хотите удалить:\n{item_path}", QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            try:
                if self.model.remove(index):
                    self.model.revert()
                    self.update_create_folder_button_state()
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", f"Ошибка при удалении файла: {str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FileListApp()
    window.show()
    sys.exit(app.exec_())
