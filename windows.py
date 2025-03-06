import time

from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QLabel, QDialog,
    QComboBox, QLineEdit, QFileDialog, QSpinBox, QMessageBox, QScrollArea
)
import sys
from PyQt6.QtCore import Qt
from mvsep_handlers import get_separation_types, create_separation, get_result

# Универсальный стиль для кнопок и полей ввода (увеличены размеры)
button_style = "font-size: 18px; padding: 20px; min-width: 300px;"  # Стиль для кнопок
input_style = "font-size: 18px; padding: 15px; min-width: 300px;"  # Стиль для текстовых полей и других элементов
# Устанавливаем стиль для текста
label_style = "font-size: 14px;"

combo_style = """
QComboBox {
    font-size: 18px; 
    padding: 15px; 
    min-width: 300px;
}

QComboBox QAbstractItemView {
    min-width: 300px; 
    font-size: 18px;
    padding: 10px;
}
"""

# Стиль для фона диалогов
dialog_background = """
    background: linear-gradient(to bottom, blue, white);
    border: none;
    margin: 0;
    padding: 0;
"""

stylesheet = """
QWidget {
    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1, 
                                stop: 0 #0176B3, stop: 0.5 #1E9BDC, stop: 1 #FFFFFF);
}
"""


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MVSep")
        self.setGeometry(100, 100, 400, 400)

        # Основной вертикальный layout
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Центрируем элементы по вертикали и горизонтали

        self.hash_label = QLabel("MVSep")
        self.hash_label.setStyleSheet("font-size: 28px;")
        self.setStyleSheet(stylesheet)
        # Добавляем вертикальный layout для кнопок
        button_layout = QVBoxLayout()
        button_layout.setSpacing(10)  # Уменьшаем расстояние между кнопками
        button_layout.addWidget(self.hash_label)
        self.get_types_button = QPushButton("Get Separation Types", self)
        self.get_types_button.setStyleSheet(button_style)
        self.get_types_button.clicked.connect(self.show_separation_types)
        button_layout.addWidget(self.get_types_button, Qt.AlignmentFlag.AlignCenter)

        self.create_sep_button = QPushButton("Create Separation", self)
        self.create_sep_button.setStyleSheet(button_style)
        self.create_sep_button.clicked.connect(self.show_create_separation)
        button_layout.addWidget(self.create_sep_button, Qt.AlignmentFlag.AlignCenter)

        self.get_result_button = QPushButton("Get Separation Result", self)
        self.get_result_button.setStyleSheet(button_style)
        self.get_result_button.clicked.connect(self.show_get_result)
        button_layout.addWidget(self.get_result_button, Qt.AlignmentFlag.AlignCenter)

        self.quit_button = QPushButton("Quit", self)
        self.quit_button.setStyleSheet(button_style)
        self.quit_button.clicked.connect(self.close)
        button_layout.addWidget(self.quit_button, Qt.AlignmentFlag.AlignCenter)

        # Добавляем button_layout в основной layout
        main_layout.addLayout(button_layout)

        # Устанавливаем основной layout
        self.setLayout(main_layout)

    def show_separation_types(self):
        # Создаем форму для отображения типов разделения
        separation_dialog = QDialog(self)
        separation_dialog.setWindowTitle("Separation Types")

        # Получаем и сортируем данные
        self.data = get_separation_types.get_separation_types()
        sorted_data = {k: v for k, v in sorted(self.data.items())}

        # Создаем QScrollArea для прокрутки
        scroll_area = QScrollArea(separation_dialog)
        scroll_area.setWidgetResizable(True)

        # Создаем контейнер для QLabel, чтобы использовать его в ScrollArea
        label_widget = QWidget()
        label_layout = QVBoxLayout(label_widget)

        # Формируем строки данных и добавляем их в layout как QLabel
        for key, value in sorted_data.items():
            label = QLabel(f"{key}: {value}", label_widget)
            label.setStyleSheet(label_style)  # Применяем стиль для текста
            label_layout.addWidget(label)

        # Устанавливаем контейнер с QLabel в ScrollArea
        scroll_area.setWidget(label_widget)

        # Создаем кнопку для закрытия формы
        close_button = QPushButton("Close", separation_dialog)
        close_button.setStyleSheet(button_style)  # Применяем стиль для кнопок
        close_button.clicked.connect(separation_dialog.accept)

        # Создаем основной layout и добавляем в него ScrollArea и кнопку
        layout = QVBoxLayout(separation_dialog)
        layout.addWidget(scroll_area)
        layout.addWidget(close_button)

        # Устанавливаем layout в диалоговое окно
        separation_dialog.setLayout(layout)

        # Отображаем диалоговое окно
        separation_dialog.exec()

    def show_create_separation(self):
        dialog = CreateSeparationDialog(self)
        dialog.exec()

    def show_get_result(self):
        dialog = GetResultDialog(self)
        dialog.exec()


class GetResultDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Get Separation Result")
        self.setGeometry(150, 150, 400, 200)

        layout = QVBoxLayout()

        # Лейбл и поле для ввода хеша
        self.hash_label = QLabel("Enter Hash")
        self.hash_input = QLineEdit()
        self.hash_input.setPlaceholderText("Enter the hash to check")
        self.hash_input.setStyleSheet(input_style)
        layout.addWidget(self.hash_label)
        layout.addWidget(self.hash_input)

        # Кнопка для проверки
        self.check_button = QPushButton("Check")
        self.check_button.setStyleSheet(button_style)
        self.check_button.clicked.connect(self.check_hash)
        layout.addWidget(self.check_button)

        self.setLayout(layout)

    def check_hash(self):
        # Получаем введенный хеш
        hash_value = self.hash_input.text().strip()

        if not hash_value:
            QMessageBox.warning(self, "Input Error", "Please enter a valid hash.")
            return

        # Проверка статуса хеша
        result = self.check_status(hash_value)

        # Если статус успешен, открываем диалог для выбора папки
        if result["success"]:
            folder_path = QFileDialog.getExistingDirectory(self, "Select Folder to Save")
            if folder_path:
                # Получаем результат
                result_text = get_result.get_result(hash_value, folder_path)
                if result_text != "":
                    # Выводим текстовый результат в диалоге
                    self.show_result(result_text)
        else:
            # Если произошла ошибка, показываем сообщение
            QMessageBox.warning(self, "Error", "An error occurred while retrieving file data.")

    def check_status(self, hash_value):
        success, data = get_result.check_result(hash_value)
        return {"success": success}  # Успешный результат

    def show_result(self, result_text):
        # Показываем результат в новом окне с текстом
        QMessageBox.information(self, "Result", result_text)

class CreateSeparationDialog(QDialog):
    def __init__(self, parent=None):
        self.selected_file = ""

        super().__init__(parent)
        self.setWindowTitle("Create Separation")
        self.setGeometry(150, 150, 400, 400)
        layout = QVBoxLayout()

        # Стиль текста для лейблов
        label_style = "font-size: 16px;"

        # Поле выбора типа сепарации
        self.type_label = QLabel("Separation Type")
        self.type_label.setStyleSheet(label_style)

        self.data = get_separation_types.get_separation_types()

        # Сортируем словарь по ключу
        sorted_data = {k: v for k, v in sorted(self.data.items())}

        # Инициализируем QComboBox
        self.type_combo = QComboBox(self)
        value = sorted_data.values()
        # Добавляем элементы в комбобокс
        self.type_combo.addItems(value)

        # Настроим обработчик для выбора
        self.type_combo.currentIndexChanged.connect(self.on_selection_change)

        self.type_combo.setStyleSheet(combo_style)
        layout.addWidget(self.type_label)
        layout.addWidget(self.type_combo)

        # Поле для API Token
        self.api_label = QLabel("API Token")
        self.api_label.setStyleSheet(label_style)
        self.api_input = QLineEdit()
        self.api_input.setStyleSheet(input_style)
        layout.addWidget(self.api_label)
        layout.addWidget(self.api_input)

        # Добавляем дополнительные опции 1, 2, 3 (с QSpinBox)
        self.option1_label = QLabel("Additional Option 1")
        self.option1_label.setStyleSheet(label_style)
        self.option1 = QSpinBox()
        self.option1.setRange(0, 1)  # Диапазон от 1 до 3
        self.option1.setValue(0)  # По умолчанию 1
        self.option1.setStyleSheet(input_style)
        layout.addWidget(self.option1_label)
        layout.addWidget(self.option1)

        self.option2_label = QLabel("Additional Option 2")
        self.option2_label.setStyleSheet(label_style)
        self.option2 = QSpinBox()
        self.option2.setRange(0, 1)  # Диапазон от 1 до 3
        self.option2.setValue(0)  # По умолчанию 1
        self.option2.setStyleSheet(input_style)
        layout.addWidget(self.option2_label)
        layout.addWidget(self.option2)

        # Кнопка для выбора файла
        self.file_button = QPushButton("Select File")
        self.file_button.setStyleSheet(button_style)
        self.file_button.clicked.connect(self.select_file)
        layout.addWidget(self.file_button)

        # Кнопка для создания сепарации
        self.create_button = QPushButton("Create Separation")
        self.create_button.setStyleSheet(button_style)
        self.create_button.clicked.connect(self.process_separation)
        layout.addWidget(self.create_button)

        self.setLayout(layout)

    def select_file(self):
        # Открываем диалог для выбора файла
        file_path, _ = QFileDialog.getOpenFileName(self, "Select File", "", "Audio Files (*.mp3 *.wav)")
        if file_path:
            self.selected_file = file_path
            print(f"File selected: {self.selected_file}")

    def on_selection_change(self, index):
        # Получаем выбранный текст
        selected_item = self.type_combo.currentText()

        # Ищем соответствующий ключ для выбранного значения
        for key, value in self.data.items():
            if value == selected_item:
                self.selected_key = key
                print(f"Selected key: {self.selected_key} - {selected_item}")
                break

    def process_separation(self):
        for key, value in self.data.items():
            if value == self.type_combo.currentText():
                self.selected_key = key
                break
        separation_type = self.selected_key
        api_token = self.api_input.text()
        option1 = self.option1.value()
        option2 = self.option2.value()
        path = self.selected_file

        # Очистим стиль полей перед проверкой
        self.clear_styles()

        # Валидация
        if not path:  # Если файл не выбран
            self.file_button.setStyleSheet("background-color: red; font-size: 18px; padding: 20px; min-width: 300px;")  # Подсвечиваем кнопку красным
        if not api_token:  # Если API токен пустой
            self.api_input.setStyleSheet("border: 2px solid red; font-size: 18px; padding: 15px; min-width: 300px;")
        if not separation_type:  # Если тип сепарации не выбран
            self.type_combo.setStyleSheet(f"border: 2px solid red; {input_style}")

        # Проверка: если есть ошибки, не продолжаем процесс
        if not path or not api_token or not separation_type:
            return

        # Пытаемся начать сепарацию (например, сгенерировать хеш или ошибку)
        result = self.start_separation(separation_type, api_token, option1, option2, path)
        if 'hash' in result:
            folder_path = QFileDialog.getExistingDirectory(self, "Select Folder to Save")
            if folder_path:
                i = 0
                while i < 180:
                    # Получаем результат
                    result_text = get_result.get_result(result['hash'], folder_path)
                    if result_text != "":
                        # Выводим текстовый результат в диалоге
                        self.show_result(result_text)
                        break
                    else:
                        i += 1
                        time.sleep(1)

    def show_result(self, result_text):
        # Показываем результат в новом окне с текстом
        QMessageBox.information(self, "Result", result_text)

    def clear_styles(self):
        # Сброс стилей
        self.file_button.setStyleSheet(button_style)
        self.api_input.setStyleSheet(input_style)
        self.type_combo.setStyleSheet(input_style)

    def start_separation(self, separation_type, api_token, option1, option2, path):
        hash, status_code = create_separation.create_separation(path, api_token, separation_type, option1, option2)
        if status_code == 200:
            return {"success": True, "hash": hash}  # Успех с хешем
        else:
            return {"success": False, "error": hash}


class ResultDialog(QDialog):
    def __init__(self, parent, result):
        super().__init__(parent)
        self.setWindowTitle("Separation Result")
        self.setGeometry(150, 150, 400, 200)
        layout = QVBoxLayout()

        if result["success"]:
            # Если успешный результат, показываем хеш
            self.result_label = QLabel(f"Separation Successful!\nHash: {result['hash']}")
            self.result_label.setStyleSheet(label_style)
            self.result_input = QLineEdit(result['hash'])
            self.result_input.setStyleSheet(input_style)
            self.result_input.setReadOnly(True)  # Делаем поле только для чтения
            layout.addWidget(self.result_label)
            layout.addWidget(self.result_input)
        else:
            # Если ошибка, показываем сообщение об ошибке
            self.result_label = QLabel(f"Error: {result['error']}")
            layout.addWidget(self.result_label)

        self.setLayout(layout)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())
