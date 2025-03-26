import time, os, json

from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QLabel, QDialog,
    QComboBox, QLineEdit, QFileDialog, QSpinBox, QMessageBox, QScrollArea
)
import sys
from PyQt6.QtCore import QMimeData, Qt, QThread, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QDrag

from mvsep_handlers import get_separation_types, create_separation, get_result


# директория файла
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Универсальный стиль для кнопок и полей ввода (увеличены размеры)
button_style = "font-size: 18px; padding: 20px; min-width: 300px; font-family: 'Poppins', sans-serif;"  
# Стиль Create Separetion
cs_button_style = "font-size: 18px; padding: 20px; min-width: 300px; font-family: 'Poppins', sans-serif; background-color: #0176b3; border-radius: 0.3rem;"  
input_style = "font-size: 18px; padding: 15px; min-width: 300px; font-family: 'Poppins', sans-serif;"  # Стиль для текстовых полей и других элементов
# Устанавливаем стиль для текста
label_style = "font-size: 16px; font-family: 'Poppins', sans-serif;"
combo_style = " font-size: 16px; font-family: 'Poppins'; padding: 20px; "

# Стиль для фона диалогов
dialog_background = """
    background: linear-gradient(to bottom, blue, white);
    border: none;
    margin: 0;
    padding: 0;
"""

stylesheet = """
QWidget {
    # background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1, 
                                stop: 0 #0176B3, stop: 0.5 #1E9BDC, stop: 1 #FFFFFF);
}
"""

path_hash_dict = {}
separation_n = 0

class SepThread(QThread):
    stop_separation_signal = pyqtSignal(str)

    def __init__(self, parent = None):
        super(SepThread, self).__init__(parent)
        self.hash = ""

    def run(self):
        global separation_n, path_hash_dict
        i = 0
        while i < 180:
            # Получаем результат
            output_dir = path_hash_dict[self.hash]
            result_text = get_result.get_result(self.hash, output_dir)
            print(f"i={i}; {self.hash}")
            print(path_hash_dict)
            if result_text != "":
                # Выводим текстовый результат в диалоге
                separation_n -= 1
                print("good separation break")
                print(result_text)
                self.stop_separation_signal.emit(result_text)
                break
            else:
                i += 1
                time.sleep(1)
            print()

        if i==179:
            # Выводим отрицательный результат в диалоге
            separation_n -= 1
            self.stop_separation_signal.emit("No result per 3 min.")





class DragButton(QPushButton):
    dragged = pyqtSignal() 

    def dragEnterEvent(self, e):
        print("dragEnterEvent")
        e.accept()

    def dropEvent(self, event):
        self.selected_file = ""
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                self.selected_file = file_path
            event.accept()
            self.dragged.emit()
        else:
            event.ignore()

    def mouseMoveEvent(self, e):
        if e.buttons() == Qt.MouseButton.LeftButton:
            drag = QDrag(self)
            mime = QMimeData()
            drag.setMimeData(mime)
            drag.exec(Qt.DropAction.MoveAction)



class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        

        self.setWindowTitle("Create Separation")
        self.setGeometry(50, 50, 400, 400)
        self.setFixedSize(400, 800)
        layout = QVBoxLayout()

        self.token_filename = os.path.join(BASE_DIR, "api_token.txt")
        self.selected_file = None
        self.output_dir = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop') 
        self.algorithm_fields = {}

        self.alg_opt1 = {}
        self.alg_opt2 = {}
        self.alg_opt3 = {}

        self.selected_opt1 = 0
        self.selected_opt2 = 0
        self.selected_opt3 = 0

        # Поле выбора типа сепарации
        self.type_label = QLabel("Separation Type")
        self.type_label.setStyleSheet(label_style)

        self.data, self.algorithm_fields = get_separation_types.get_separation_types()
        
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
        # ищем файл с токеном
        if os.path.isfile(self.token_filename):
            with open(self.token_filename, "r") as f: 
                api_token = f.read().strip()
                if len(api_token) == 30:
                    self.api_input.setText(api_token)

        layout.addWidget(self.api_label)
        layout.addWidget(self.api_input)

        # Ссылка для API Token
        self.api_link_label = QLabel("<a href='https://mvsep.com/ru/full_api'>Get Token</a>")
        self.api_link_label.setStyleSheet(label_style)
        self.api_link_label.setOpenExternalLinks(True)
        layout.addWidget(self.api_link_label)



        # Добавляем дополнительные опции 1, 2, 3
        self.option1_label = QLabel("Additional Option 1")
        self.option1_label.setStyleSheet(label_style)
        # Инициализируем QComboBox
        self.option1_combo = QComboBox(self)
        self.option1_combo.setStyleSheet(combo_style)
        # Настроим обработчик для выбора
        self.option1_combo.currentIndexChanged.connect(self.on_change_option1)
        layout.addWidget(self.option1_label)
        layout.addWidget(self.option1_combo)

        # Добавляем дополнительные опции 1, 2, 3
        self.option2_label = QLabel("Additional Option 2")
        self.option2_label.setStyleSheet(label_style)
        # Инициализируем QComboBox
        self.option2_combo = QComboBox(self)
        self.option2_combo.setStyleSheet(combo_style)
        # Настроим обработчик для выбора
        self.option2_combo.currentIndexChanged.connect(self.on_change_option2)
        layout.addWidget(self.option2_label)
        layout.addWidget(self.option2_combo)

        # Добавляем дополнительные опции 1, 2, 3
        self.option3_label = QLabel("Additional Option 3")
        self.option3_label.setStyleSheet(label_style)
        # Инициализируем QComboBox
        self.option3_combo = QComboBox(self)
        self.option3_combo.setStyleSheet(combo_style)
        # Настроим обработчик для выбора
        self.option3_combo.currentIndexChanged.connect(self.on_change_option3)
        layout.addWidget(self.option3_label)
        layout.addWidget(self.option3_combo)



        # Выбранный аудио файл
        self.filename_label = QLabel("Audio selected:")
        self.filename_label.setStyleSheet(label_style)
        self.filename_label.setOpenExternalLinks(True)
        layout.addWidget(self.filename_label)
        # Кнопка для выбора файла
        self.file_button = DragButton("Select File")
        self.file_button.setAcceptDrops(True)
        self.file_button.setStyleSheet(button_style)
        self.file_button.clicked.connect(self.select_file)
        self.file_button.dragged.connect(self.select_drag_file)

        layout.addWidget(self.file_button)


        # Выбранная директория
        self.output_dir_label = QLabel(f"Output Dir: {self.output_dir}")
        self.output_dir_label.setStyleSheet(label_style)
        layout.addWidget(self.output_dir_label)
        # Кнопка для выбора директории результатов
        self.output_dir_button = QPushButton("Select Output Dir")
        self.output_dir_button.setStyleSheet(button_style)
        self.output_dir_button.clicked.connect(self.select_output_dir)
        layout.addWidget(self.output_dir_button)




        # Кнопка для создания сепарации
        self.create_button = QPushButton("Create Separation")
        self.create_button.setStyleSheet(cs_button_style)
        self.create_button.clicked.connect(self.process_separation)
        layout.addWidget(self.create_button)

        self.setLayout(layout)



    def select_file(self):
        # Открываем диалог для выбора файла
        file_path, _ = QFileDialog.getOpenFileName(self, "Select File", "", "Audio Files (*.mp3 *.wav)")
        if file_path:
            self.selected_file = file_path
            print(f"File selected: {self.selected_file}")
            self.filename_label.setText(f"Audio selected: {os.path.basename(self.selected_file)}")

    def select_drag_file(self):
        self.selected_file = self.file_button.selected_file
        print(f"File selected: {self.selected_file}")
        self.filename_label.setText(f"Audio selected: {os.path.basename(self.selected_file)}")





    def on_selection_change(self, index):
        # Получаем выбранный текст
        selected_item = self.type_combo.currentText()

        # Ищем соответствующий ключ для выбранного значения
        for key, value in self.data.items():
            if value == selected_item:
                self.selected_key = key
                print(f"Selected key: {self.selected_key} - {selected_item}")
                
                selected_algorithm = self.algorithm_fields[key]
                print("Options Len:")
                print(len(selected_algorithm))
                print("Options:")
                print(selected_algorithm)

                # очищаем все ComboBox
                self.option1_combo.clear()
                self.option2_combo.clear()
                self.option3_combo.clear()
                self.option1_label.setText("Additional Option 1")
                self.option2_label.setText("Additional Option 2")
                self.option3_label.setText("Additional Option 3")

                if len(self.algorithm_fields[key]) > 0:
                    self.option1_label.setText(f"Additional Option 1: {selected_algorithm[0]['text']}")
                    self.alg_opt1 = json.loads(selected_algorithm[0]['options'])
                    # Сортируем словарь по ключу
                    sorted_data = {k: v for k, v in sorted(self.alg_opt1.items())}
                    value = sorted_data.values()
                    # Добавляем элементы в комбобокс
                    self.option1_combo.addItems(value)

                if len(self.algorithm_fields[key]) > 1:
                    self.option2_label.setText(f"Additional Option 2: {selected_algorithm[1]['text']}")
                    self.alg_opt2 = json.loads(selected_algorithm[1]['options'])
                    # Сортируем словарь по ключу
                    sorted_data = {k: v for k, v in sorted(self.alg_opt2.items())}
                    value = sorted_data.values()
                    # Добавляем элементы в комбобокс
                    self.option2_combo.addItems(value)
               
                if len(self.algorithm_fields[key]) > 2:
                    self.option3_label.setText(f"Additional Option 3: {selected_algorithm[2]['text']}")
                    self.alg_opt3 = json.loads(selected_algorithm[2]['options'])
                    # Сортируем словарь по ключу
                    sorted_data = {k: v for k, v in sorted(self.alg_opt3.items())}
                    value = sorted_data.values()
                    # Добавляем элементы в комбобокс
                    self.option3_combo.addItems(value)



                break



    def on_change_option1(self, index):
        # Получаем выбранный текст
        selected_item = self.option1_combo.currentText()
        # Ищем соответствующий ключ для выбранного значения
        for key, value in self.alg_opt1.items():
            if value == selected_item:
                self.selected_opt1 = key
                break

    def on_change_option2(self, index):
        # Получаем выбранный текст
        selected_item = self.option2_combo.currentText()
        # Ищем соответствующий ключ для выбранного значения
        for key, value in self.alg_opt2.items():
            if value == selected_item:
                self.selected_opt2 = key
                break

    def on_change_option3(self, index):
        # Получаем выбранный текст
        selected_item = self.option3_combo.currentText()
        # Ищем соответствующий ключ для выбранного значения
        for key, value in self.alg_opt3.items():
            if value == selected_item:
                self.selected_opt3 = key
                break



    def select_output_dir(self):
        # Открываем диалог для выбора файла
        self.output_dir = QFileDialog.getExistingDirectory(self, "Select Folder to Save")
        self.output_dir_label.setText(f"Output Dir: {self.output_dir}")
    
    
    
    
    
    
    
    def process_separation(self):
        global path_hash_dict, start_result, separation_n
        for key, value in self.data.items():
            if value == self.type_combo.currentText():
                self.selected_key = key
                break
        separation_type = self.selected_key
        api_token = self.api_input.text()
        option1 = self.selected_opt1
        option2 = self.selected_opt2
        option3 = self.selected_opt3
        path = self.selected_file

        # Очистим стиль полей перед проверкой
        self.clear_styles()
        # Валидация
        if not path:  # Если файл не выбран
            self.file_button.setStyleSheet("background-color: red; font-size: 18px; padding: 20px; min-width: 300px;")  # Подсвечиваем кнопку красным
        if not api_token:  # Если API токен пустой
            self.api_input.setStyleSheet("border: 2px solid red; font-size: 18px; padding: 15px; min-width: 300px;")
        else:
            # сохраним в файл
            with open(self.token_filename, "w") as f: 
                f.write(api_token)

        if not separation_type:  # Если тип сепарации не выбран
            self.type_combo.setStyleSheet(f"border: 2px solid red; {combo_style}")

        # Проверка: если есть ошибки, не продолжаем процесс
        if (path == None) or not api_token or not separation_type:
            os.system('cls')
            print("Error separation:")
            print(f"path: {path}")
            print(f"api_token: {api_token}")
            print(f"separation_type: {separation_type}")
            return

        # Пытаемся начать сепарацию (например, сгенерировать хеш или ошибку)
        result = self.start_separation(separation_type, api_token, option1, option2, option3, path)
        if 'hash' in result:
            # подключаем тред проверки хода сепарации
            path_hash_dict[result["hash"]] = self.output_dir
            start_result = result
            separation_n += 1
            self.create_button.setText(f"Create Separation: [{separation_n} in progress]")
            self.st = SepThread(self)
            self.st.stop_separation_signal.connect(self.stop_separation)
            self.st.hash = result["hash"]
            self.st.start()
            QMessageBox.information(self, "Result", f"Thread #{separation_n}\nin progress") 

    def stop_separation(self, result_text):
        global separation_n
        # завершение сепарации
        QMessageBox.information(self, "Result", result_text)        
        self.create_button.setText(f"Create Separation: [{separation_n}]")


        

    def clear_styles(self):
        # Сброс стилей
        self.file_button.setStyleSheet(button_style)
        self.api_input.setStyleSheet(input_style)
        self.type_combo.setStyleSheet(combo_style)

    def start_separation(self, separation_type, api_token, option1, option2, option3, path):
        hash, status_code = create_separation.create_separation(path, api_token, separation_type, option1, option2, option3)
        if status_code == 200:
            return {"success": True, "hash": hash}  # Успех с хешем
        else:
            return {"success": False, "error": hash}



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
