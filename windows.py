import time, os, json
import sqlite3, requests
from datetime import datetime

from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QGridLayout, QLabel, QDialog,
    QComboBox, QLineEdit, QFileDialog, QTableWidget, QMessageBox, QScrollArea, QTableWidgetItem
)
import sys
from PyQt6.QtCore import QMimeData, Qt, QThread, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QDrag

from mvsep_handlers import get_separation_types, create_separation, get_result


# директория файла
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
connection = sqlite3.connect(os.path.join(BASE_DIR, 'jobs.db'), check_same_thread=False)


# Универсальный стиль для кнопок и полей ввода (увеличены размеры)
button_style = "font-size: 18px; padding: 20px; min-width: 300px; font-family: 'Poppins', sans-serif;"  
# Стиль Create Separetion
cs_button_style = "font-size: 18px; padding: 20px; min-width: 300px; font-family: 'Poppins', sans-serif; background-color: #0176b3; border-radius: 0.3rem;"  
input_style = "font-size: 18px; padding: 15px; min-width: 300px; font-family: 'Poppins', sans-serif;"  # Стиль для текстовых полей и других элементов
# Устанавливаем стиль для текста
label_style = "font-size: 16px; font-family: 'Poppins', sans-serif;"
small_label_style = "font-size: 12px; font-family: 'Poppins', sans-serif;"
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

    def __init__(self, api_token = None, data_table = None, base_dir_label = None):
        super(SepThread, self).__init__()
        self.data_table = data_table
        self.api_token = api_token
        self.base_dir_label = base_dir_label

    def run(self):
        # Создаем подключение к базе данных (файл my_database.db будет создан)
        # self.connection = sqlite3.connect(os.path.join(BASE_DIR, 'jobs.db'), check_same_thread=False)
        global connection
        self.cursor = connection.cursor()

        while True:

            # проверяем запущенные процессы
            # self.cursor.execute('INSERT INTO Jobs (start_time, update_time, filename, out_dir, hash[5], status[6], separation, option1, option2, option3) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', (int(time.time()), int(time.time()), path, self.output_dir, "", "Added", separation_type, option1, option2, option3))
            self.cursor.execute('SELECT * FROM Jobs ORDER BY id DESC')
            jobs = self.cursor.fetchall()
            print("Job: ")
            for row, job in enumerate(jobs):
                # self.data_table.setHorizontalHeaderLabels(["ID", "Start Time", "FileName", "Out Dir", "Separation Type", "Adv.Opt #1", "Adv.Opt #2", "Adv.Opt #3", "Status", "Update Status"])
                # self.data_table.setHorizontalHeaderLabels(["ID", "FileName", "Separation Type""Status"])
                job_id = int(job[0])
                # self.data_table.setItem(row, 0, QTableWidgetItem(str(job_id)))
                # start_date = datetime.strptime(str(job[1]), '%Y-%m-%d %H:%M')
                start_date = datetime.fromtimestamp(job[1])
                start_date = str(start_date.strftime('%Y-%m-%d %H:%M'))

                file_name = os.path.basename(job[3])
                self.data_table.setItem(row, 0, QTableWidgetItem(file_name))
                
                out_dir = job[4]
                separation_type = str(job[7])
                self.data_table.setItem(row, 1, QTableWidgetItem(separation_type)) # separation
                """
                self.data_table.setItem(row, 5, QTableWidgetItem(job[8])) #  option1
                self.data_table.setItem(row, 6, QTableWidgetItem(job[9])) #  option2
                self.data_table.setItem(row, 7, QTableWidgetItem(job[10])) #  option 3
                """
                status = str(job[6])
                self.data_table.setItem(row, 2, QTableWidgetItem(status)) # status
                update_time = datetime.fromtimestamp(job[2])
                update_time = str(update_time.strftime('%H:%M:%S'))



                if job[6] == "Added":
                    # Пытаемся начать сепарацию (например, сгенерировать хеш или ошибку)
                    self.base_dir_label.setText(f"Token: {self.api_token}")

                    hash, status_code = create_separation.create_separation(job[3], self.api_token, separation_type, job[8], job[9], job[10])
                    
                    if status_code == 200: # Успех с хешем
                        self.cursor.execute('UPDATE Jobs SET hash = ? WHERE id = ?', (hash, job[0]))  
                        self.cursor.execute('UPDATE Jobs SET status = ? WHERE id = ?', ("Process", job[0]))
                        self.cursor.execute('UPDATE Jobs SET update_time = ? WHERE id = ?', (int(time.time()), job[0]))   

                        self.cursor.execute('INSERT INTO Log (job_id, update_time, action, comment) VALUES (?, ?, ?, ?)', (job_id, int(time.time()), "Added -> Process", ""))
                    
                    else:
                        self.cursor.execute('INSERT INTO Log (job_id, update_time, action, comment) VALUES (?, ?, ?, ?)', (job_id, int(time.time()), "Error Start Process", f"response.content: {hash}"))
                        print("error start process")
                        print(hash)

    

                
                # подключаем тред проверки хода сепарации
                if job[6] == "Process":
                        self.cursor.execute('UPDATE Jobs SET update_time = ? WHERE id = ?', (int(time.time()), job[0]))
                        self.cursor.execute('INSERT INTO Log (job_id, update_time, action, comment) VALUES (?, ?, ?, ?)', (job_id, int(time.time()), "Process", f""))


                        params = {'hash': job[5]}
                        response = requests.get('https://mvsep.com/api/separation/get', params=params)
                        data = json.loads(response.content.decode('utf-8'))
                        
                        if data['success']:
                            self.cursor.execute('INSERT INTO Log (job_id, update_time, action, comment) VALUES (?, ?, ?, ?)', (job_id, int(time.time()), "Process -> Success", f""))

                            files = []
                            try:
                                files = data['data']['files']
                            except KeyError:
                                pass
                                self.cursor.execute('INSERT INTO Log (job_id, update_time, action, comment) VALUES (?, ?, ?, ?)', (job_id, int(time.time()), "Process -> No Files", f""))

                            for file_info in files:
                                url = file_info['url'].replace('\\/', '/')  # Correct slashes
                                filename = file_info['download']  # File name for saving
                                # download_file(url, filename, save_path)
                                self.cursor.execute('UPDATE Jobs SET status = ? WHERE id = ?', ("Download", job[0]))
                                self.cursor.execute('UPDATE Jobs SET update_time = ? WHERE id = ?', (int(time.time()), job[0]))                    
                                self.cursor.execute('INSERT INTO Log (job_id, update_time, action, comment) VALUES (?, ?, ?, ?)', (job_id, int(time.time()), "Process -> Download", f"filename: {filename}"))

                                print(f"Start download: {url}")
                                response = requests.get(url)
                                if response.status_code == 200:
                                    # Ensure the directory exists
                                    if not os.path.exists(job[4]):
                                        os.makedirs(job[4])
                                    file_path = os.path.join(job[4], filename)
                                    # Save the content of the response to the file
                                    with open(file_path, 'wb') as f:
                                        f.write(response.content)
                                        self.cursor.execute('UPDATE Jobs SET status = ? WHERE id = ?', ("Complete", job[0]))
                                    self.cursor.execute('INSERT INTO Log (job_id, update_time, action, comment) VALUES (?, ?, ?, ?)', (job_id, int(time.time()), "Process -> Complete", f"filename: {filename}"))


                        else:
                            self.cursor.execute('UPDATE Jobs SET status = ? WHERE id = ?', ("Error", job[0]))
                            self.cursor.execute('INSERT INTO Log (job_id, update_time, action, comment) VALUES (?, ?, ?, ?)', (job_id, int(time.time()), "Process -> Error", f""))

                    
                    


            self.data_table.resizeColumnsToContents()
            connection.commit()
            time.sleep(1)
            
        







class DragButton(QPushButton):
    dragged = pyqtSignal() 

    def dragEnterEvent(self, e):
        print("dragEnterEvent")
        e.accept()

    def dropEvent(self, event):
        self.selected_files = []
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                self.selected_files.append(file_path)
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
        
        # Создаем подключение к базе данных (файл my_database.db будет создан)
        global connection
        self.cursor = connection.cursor()

        # Создаем таблицу Jobs
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS Jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        start_time INTEGER,
        update_time INTEGER,
        filename TEXT NOT NULL,
        out_dir TEXT NOT NULL,
        hash TEXT NOT NULL,
        status TEXT NOT NULL,
        separation INTEGER,
        option1 TEXT NOT NULL,
        option2 TEXT NOT NULL,
        option3 TEXT NOT NULL
        )
        ''')
        connection.commit()


        # Создаем таблицу Log
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS Log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER,
        update_time INTEGER,
        action TEXT NOT NULL,
        comment TEXT NOT NULL
        )
        ''')
        connection.commit()



        self.setWindowTitle("Create Separation")
        self.setGeometry(50, 50, 400, 400)
        self.setFixedSize(800, 800)
        layout = QGridLayout()

        self.token_filename = os.path.join(BASE_DIR, "api_token.txt")
        self.selected_files = []
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
        layout.addWidget(self.type_label, 0, 0)
        layout.addWidget(self.type_combo, 1, 0)
        


        self.data_table = QTableWidget(self)  # Create a table
        self.data_table.setColumnCount(3)     #Set three columns
        self.data_table.setRowCount(24) 
        layout.addWidget(self.data_table, 0, 1, 0, 10)
        self.data_table.setHorizontalHeaderLabels(["FileName", "Separation Type", "Status"])
        self.data_table.setMinimumWidth(380)
        self.data_table.resizeColumnsToContents()



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

        layout.addWidget(self.api_label, 2, 0)
        layout.addWidget(self.api_input, 3, 0)

        # Ссылка для API Token
        self.api_link_label = QLabel("<a href='https://mvsep.com/ru/full_api'>Get Token</a>")
        self.api_link_label.setStyleSheet(label_style)
        self.api_link_label.setOpenExternalLinks(True)
        layout.addWidget(self.api_link_label, 4, 0)



        # Добавляем дополнительные опции 1, 2, 3
        self.option1_label = QLabel("Additional Option 1")
        self.option1_label.setStyleSheet(label_style)
        # Инициализируем QComboBox
        self.option1_combo = QComboBox(self)
        self.option1_combo.setStyleSheet(combo_style)
        # Настроим обработчик для выбора
        self.option1_combo.currentIndexChanged.connect(self.on_change_option1)
        layout.addWidget(self.option1_label, 5, 0)
        layout.addWidget(self.option1_combo, 6, 0)

        # Добавляем дополнительные опции 1, 2, 3
        self.option2_label = QLabel("Additional Option 2")
        self.option2_label.setStyleSheet(label_style)
        # Инициализируем QComboBox
        self.option2_combo = QComboBox(self)
        self.option2_combo.setStyleSheet(combo_style)
        # Настроим обработчик для выбора
        self.option2_combo.currentIndexChanged.connect(self.on_change_option2)
        layout.addWidget(self.option2_label,7,0)
        layout.addWidget(self.option2_combo,8,0)

        # Добавляем дополнительные опции 1, 2, 3
        self.option3_label = QLabel("Additional Option 3")
        self.option3_label.setStyleSheet(label_style)
        # Инициализируем QComboBox
        self.option3_combo = QComboBox(self)
        self.option3_combo.setStyleSheet(combo_style)
        # Настроим обработчик для выбора
        self.option3_combo.currentIndexChanged.connect(self.on_change_option3)
        layout.addWidget(self.option3_label,9,0)
        layout.addWidget(self.option3_combo,10,0)



        # Выбранный аудио файл
        self.filename_label = QLabel("Audio selected:")
        self.filename_label.setStyleSheet(label_style)
        self.filename_label.setOpenExternalLinks(True)
        layout.addWidget(self.filename_label,11,0)
        # Кнопка для выбора файла
        self.file_button = DragButton("Select File")
        self.file_button.setAcceptDrops(True)
        self.file_button.setStyleSheet(button_style)
        self.file_button.clicked.connect(self.select_file)
        self.file_button.dragged.connect(self.select_drag_file)

        layout.addWidget(self.file_button,12,0)


        # Выбранная директория
        self.output_dir_label = QLabel(f"Output Dir: {self.output_dir}")
        self.output_dir_label.setStyleSheet(label_style)
        layout.addWidget(self.output_dir_label,13,0)
        # Кнопка для выбора директории результатов
        self.output_dir_button = QPushButton("Select Output Dir")
        self.output_dir_button.setStyleSheet(button_style)
        self.output_dir_button.clicked.connect(self.select_output_dir)
        layout.addWidget(self.output_dir_button,14,0)




        # Кнопка для создания сепарации
        self.create_button = QPushButton("Create Separation")
        self.create_button.setStyleSheet(cs_button_style)
        self.create_button.clicked.connect(self.process_separation)
        layout.addWidget(self.create_button,15,0)

        # Base Dir
        self.base_dir_label = QLabel(f"Base Dir: {BASE_DIR}")
        self.base_dir_label.setStyleSheet(small_label_style)
        layout.addWidget(self.base_dir_label,16,0)


        self.setLayout(layout)
        # self.connection.close()

        # подключаем тред проверки хода сепарации
        
        self.st = SepThread(api_token = self.api_input.text(), data_table = self.data_table, base_dir_label=self.base_dir_label)
        self.st.start()














    def select_file(self):
        # Открываем диалог для выбора файла
        self.selected_files = QFileDialog.getOpenFileNames(self, "Select File", "", "Audio Files (*.mp3 *.wav)")
        self.selected_files = self.selected_files[0]
        print(f"Files selected:")
        print(self.selected_files)
        if len(self.selected_files) > 0:
            self.filename_label.setText(f"Audio selected: {os.path.basename(self.selected_files[0])}")

    def select_drag_file(self):
        self.selected_files = self.file_button.selected_files
        print(f"Files selected:")
        print(self.selected_files)
        if len(self.selected_files) > 0:
            self.filename_label.setText(f"Audio selected: {os.path.basename(self.selected_files[0])}")





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
        global path_hash_dict, separation_n, connection

        for key, value in self.data.items():
            if value == self.type_combo.currentText():
                self.selected_key = key
                break
        separation_type = self.selected_key
        api_token = self.api_input.text()
        option1 = self.selected_opt1
        option2 = self.selected_opt2
        option3 = self.selected_opt3

        # Очистим стиль полей перед проверкой
        self.clear_styles()
        # Валидация
        if len(self.selected_files) == 0:  # Если файл не выбран
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
        if (len(self.selected_files) == 0) or not api_token or not separation_type:
            os.system('cls')
            print("Error separation:")
            print(f"api_token: {api_token}")
            print(f"separation_type: {separation_type}")
            return

        
        self.st.api_token = self.api_input.text()
        """
        start_time INTEGER,
        update_time INTEGER,
        filename TEXT NOT NULL,
        out_dir TEXT NOT NULL,
        hash TEXT NOT NULL,
        status TEXT NOT NULL,
        separation INTEGER,
        option1 TEXT NOT NULL,
        option2 TEXT NOT NULL,
        option3 TEXT NOT NULL,
        
        """
        for file in self.selected_files:
            # Добавляем новое задание
            self.cursor.execute('INSERT INTO Jobs (start_time, update_time, filename, out_dir, hash, status, separation, option1, option2, option3) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', (int(time.time()), int(time.time()), file, self.output_dir, "", "Added", separation_type, option1, option2, option3))
            connection.commit()

            self.cursor.execute('SELECT * FROM Jobs ORDER BY id DESC LIMIT 0,1')
            jobs = self.cursor.fetchall()
            for job in jobs:
                job_id = int(job[0])
            print(f"job_id: {job_id}")
            
            
            # Логируем
            """
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER,
            update_time INTEGER,
            action TEXT NOT NULL,
            comment TEXT NOT NULL
            
            """
            self.cursor.execute('INSERT INTO Log (job_id, update_time, action, comment) VALUES (?, ?, ?, ?)', (job_id, int(time.time()), "Added", ""))
            connection.commit()


        # Пытаемся начать сепарацию (например, сгенерировать хеш или ошибку)
        """
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
        """
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
