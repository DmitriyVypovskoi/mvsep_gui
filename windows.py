import time, os, json
import sqlite3, requests
from datetime import datetime

from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QAbstractItemView, QGridLayout, QLabel, QDialog,
    QComboBox, QLineEdit, QFileDialog, QTableWidget, QMessageBox, QScrollArea, QTableWidgetItem, QTextEdit
)
import sys
from PyQt6.QtCore import QMimeData, Qt, QThread, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QDrag
from PyQt6.QtGui import QIcon

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
                    # self.base_dir_label.setText(f"Token: {self.api_token}")

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

                    
                    


            # self.data_table.resizeColumnsToContents()
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

        icon_path = os.path.join(BASE_DIR, 'mvsep.ico')
        self.setWindowIcon(QIcon(icon_path))
        
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
        self.setFixedSize(740, 600)
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

        self.selected_algoritms_list = []

        self.data, self.algorithm_fields = get_separation_types.get_separation_types()
        

        """
████████    █████    █████     ██        ███████   
   ██      ██   ██   ██   ██   ██        ██        
   ██      ███████   █████     ██        █████     
   ██      ██   ██   ██   ██   ██   ██   ██        
   ██      ██   ██   █████     ██████    ███████           
        """
        # Create a table
        self.data_table = QTableWidget(self)  
        self.data_table.setColumnCount(3)     #Set three columns
        self.data_table.setColumnWidth(0, 185)
        self.data_table.setColumnWidth(1, 100)
        self.data_table.setColumnWidth(2, 50)
        self.data_table.setRowCount(10) 
        self.data_table.setHorizontalHeaderLabels(["FileName", "Separation Type", "Status"])
        self.data_table.setMinimumWidth(350)
        self.data_table.setMinimumHeight(350)
        #self.data_table.setAutoScroll(True)
        self.data_table.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)

        layout.addWidget(self.data_table, 0, 1, 0, 7, alignment=Qt.AlignmentFlag.AlignTop)


        self.file_list_label = QLabel("Selected Files:")
        self.file_list_label.setStyleSheet(label_style)
        layout.addWidget(self.file_list_label, 7, 1, alignment=Qt.AlignmentFlag.AlignTop)
        # текстовое поле для списка файлов
        self.file_list_text = QTextEdit(self)
        self.file_list_text.toPlainText()
        layout.addWidget(self.file_list_text, 8, 1, 3, 1, alignment=Qt.AlignmentFlag.AlignTop)



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

        layout.addWidget(self.api_label, 0, 0)
        layout.addWidget(self.api_input, 1, 0)

        # Ссылка для API Token
        self.api_link_label = QLabel("<a href='https://mvsep.com/ru/full_api'>Get Token</a>")
        self.api_link_label.setStyleSheet(label_style)
        self.api_link_label.setOpenExternalLinks(True)
        layout.addWidget(self.api_link_label, 2, 0)

        # Кнопка для запуска мастера
        self.master_button = QPushButton("Algorithms Master")
        self.master_button.setAcceptDrops(True)
        self.master_button.setStyleSheet(button_style)
        self.master_button.clicked.connect(self.start_master)
        layout.addWidget(self.master_button, 3, 0)


        # Выбранный аудио файл
        self.filename_label = QLabel("Audio selected:")
        self.filename_label.setStyleSheet(label_style)
        self.filename_label.setOpenExternalLinks(True)
        layout.addWidget(self.filename_label, 4, 0)
        # Кнопка для выбора файла
        self.file_button = DragButton("Select File")
        self.file_button.setAcceptDrops(True)
        self.file_button.setStyleSheet(button_style)
        self.file_button.clicked.connect(self.select_file)
        self.file_button.dragged.connect(self.select_drag_file)

        layout.addWidget(self.file_button, 5, 0)


        # Очистка выбранных файлов
        self.clear_files_button = QPushButton("Clear Files")
        self.clear_files_button.setStyleSheet(button_style)
        self.clear_files_button.clicked.connect(self.clear_files)
        layout.addWidget(self.clear_files_button, 6, 0)



        # Выбранная директория
        self.output_dir_label = QLabel(f"Output Dir: {self.output_dir}")
        self.output_dir_label.setStyleSheet(label_style)
        layout.addWidget(self.output_dir_label, 7, 0)
        # Кнопка для выбора директории результатов
        self.output_dir_button = QPushButton("Select Output Dir")
        self.output_dir_button.setStyleSheet(button_style)
        self.output_dir_button.clicked.connect(self.select_output_dir)
        layout.addWidget(self.output_dir_button, 8, 0)




        # Кнопка для создания сепарации
        self.create_button = QPushButton("Create Separation")
        self.create_button.setStyleSheet(cs_button_style)
        self.create_button.clicked.connect(self.process_separation)
        layout.addWidget(self.create_button,9,0)

        # Base Dir
        self.base_dir_label = QLabel(f"Base Dir: {BASE_DIR}")
        self.base_dir_label.setStyleSheet(small_label_style)
        layout.addWidget(self.base_dir_label,10,0)


        self.setLayout(layout)
        # self.connection.close()

        # подключаем тред проверки хода сепарации
        
        self.st = SepThread(api_token = self.api_input.text(), data_table = self.data_table, base_dir_label=self.base_dir_label)
        self.st.start()


    def clear_files(self):
        self.selected_files = []
        self.filename_label.setText(f"No Audio selected:")
        # добавляем в TextEdit
        self.file_list_text.setText("")



    def select_file(self):
        # Открываем диалог для выбора файла
        self.selected_files = QFileDialog.getOpenFileNames(self, "Select File", "", "Audio Files (*.mp3 *.wav)")
        self.selected_files = self.selected_files[0]
        print(f"Files selected:")
        print(self.selected_files)
        if len(self.selected_files) > 0:
            self.filename_label.setText(f"Audio selected: {os.path.basename(self.selected_files[0])}")
            # добавляем в TextEdit
            self.file_list_text.setText("")
            selected_files_text = "\n".join(self.selected_files)
            self.file_list_text.setText(selected_files_text)

            self.create_button.setText("Create Separation")



    def select_drag_file(self):
        self.selected_files = self.file_button.selected_files
        print(f"Files selected:")
        print(self.selected_files)
        if len(self.selected_files) > 0:
            self.filename_label.setText(f"Audio selected: {os.path.basename(self.selected_files[0])}...")
            # добавляем в TextEdit
            self.file_list_text.setText("")
            selected_files_text = "\n".join(self.selected_files)
            self.file_list_text.setText(selected_files_text)

            self.create_button.setText("Create Separation")




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

        api_token = self.api_input.text()

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

        if len(self.selected_algoritms_list) == 0:  # Если тип сепарации не выбран
            self.master_button.setStyleSheet(f"border: 2px solid red; {combo_style}")

        # Проверка: если есть ошибки, не продолжаем процесс
        if (len(self.selected_files) == 0) or not api_token or (len(self.selected_algoritms_list) == 0):
            os.system('cls')
            print("Error separation:")
            print(f"api_token: {api_token}")
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
        if len(self.selected_algoritms_list) > 0:
            for new_item in self.selected_algoritms_list:
                separation_type = new_item["selected_key"]
                option1 = new_item["selected_opt1"]
                option2 = new_item["selected_opt2"]
                option3 = new_item["selected_opt3"]

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
                    self.cursor.execute('INSERT INTO Log (job_id, update_time, action, comment) VALUES (?, ?, ?, ?)', (job_id, int(time.time()), "Added from Master", ""))
                    connection.commit()

            self.selected_algoritms_list = []


        else:
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



        self.create_button.setText("Create Separation +")


    def stop_separation(self, result_text):
        global separation_n
        # завершение сепарации
        QMessageBox.information(self, "Result", result_text)        
        self.create_button.setText(f"Create Separation: [{separation_n}]")


    def clear_styles(self):
        # Сброс стилей
        self.master_button.setStyleSheet(button_style)
        self.file_button.setStyleSheet(button_style)
        self.api_input.setStyleSheet(input_style)


    def start_separation(self, separation_type, api_token, option1, option2, option3, path):
        hash, status_code = create_separation.create_separation(path, api_token, separation_type, option1, option2, option3)
        if status_code == 200:
            return {"success": True, "hash": hash}  # Успех с хешем
        else:
            return {"success": False, "error": hash}


    """
███    ███    █████     ██████   ████████   ███████   ███████    
██ █  █ ██   ██   ██   ██           ██      ██        ██    ██   
██  ██  ██   ███████    █████       ██      █████     ███████    
██      ██   ██   ██        ██      ██      ██        ██  ██     
██      ██   ██   ██   ██████       ██      ███████   ██    ██   
    """


    def start_master(self):
        # Создаем форму для отображения типов разделения
        separation_dialog = QDialog(self)
        separation_dialog.setWindowTitle("Separation Types")
        # separation_dialog.setGeometry(50, 50, 400, 400)
        separation_dialog.setFixedSize(740, 600)


        layout = QGridLayout(separation_dialog)

        
        # Поле выбора типа сепарации
        self.type_label_master = QLabel("Separation Type")
        self.type_label_master.setStyleSheet(label_style)
        
        self.data, self.algorithm_fields = get_separation_types.get_separation_types()
        
        # Сортируем словарь по ключу
        sorted_data = {k: v for k, v in sorted(self.data.items())}

        # Инициализируем QComboBox
        self.type_combo_master = QComboBox(self)
        value = sorted_data.values()
        # Добавляем элементы в комбобокс
        self.type_combo_master.addItems(value)

        # Настроим обработчик для выбора
        self.type_combo_master.currentIndexChanged.connect(self.on_selection_master_change)

        self.type_combo_master.setStyleSheet(combo_style)
        layout.addWidget(self.type_label_master, 0, 0)
        layout.addWidget(self.type_combo_master, 1, 0)



        # Добавляем дополнительные опции 1, 2, 3
        self.option1_label_master = QLabel("Additional Option 1")
        self.option1_label_master.setStyleSheet(label_style)
        # Инициализируем QComboBox
        self.option1_combo_master = QComboBox(self)
        self.option1_combo_master.setStyleSheet(combo_style)
        # Настроим обработчик для выбора
        self.option1_combo_master.currentIndexChanged.connect(self.on_change_master_option1)
        layout.addWidget(self.option1_label_master, 2, 0)
        layout.addWidget(self.option1_combo_master, 3, 0)

        # Добавляем дополнительные опции 1, 2, 3
        self.option2_label_master = QLabel("Additional Option 2")
        self.option2_label_master.setStyleSheet(label_style)
        # Инициализируем QComboBox
        self.option2_combo_master = QComboBox(self)
        self.option2_combo_master.setStyleSheet(combo_style)
        # Настроим обработчик для выбора
        self.option2_combo_master.currentIndexChanged.connect(self.on_change_master_option2)
        layout.addWidget(self.option2_label_master,4,0)
        layout.addWidget(self.option2_combo_master,5,0)

        # Добавляем дополнительные опции 1, 2, 3
        self.option3_label_master = QLabel("Additional Option 3")
        self.option3_label_master.setStyleSheet(label_style)
        # Инициализируем QComboBox
        self.option3_combo_master = QComboBox(self)
        self.option3_combo_master.setStyleSheet(combo_style)
        # Настроим обработчик для выбора
        self.option3_combo_master.currentIndexChanged.connect(self.on_change_master_option3)
        layout.addWidget(self.option3_label_master,6,0)
        layout.addWidget(self.option3_combo_master,7,0)

        # Создаем кнопку для добавления алгоритма
        add_button = QPushButton("Add Algorithm", separation_dialog)
        add_button.setStyleSheet(button_style)  # Применяем стиль для кнопок
        add_button.clicked.connect(self.add_algoritm)
        layout.addWidget(add_button,8,0)



        # ПРАВЫЙ СТОЛБЕЦ
        self.algo_list_label = QLabel("Selected Algorithms:")
        self.algo_list_label.setStyleSheet(label_style)
        layout.addWidget(self.algo_list_label, 0, 1, alignment=Qt.AlignmentFlag.AlignTop)
        # текстовое поле для списка файлов
        self.algo_list_text = QTextEdit(self)
        self.algo_list_text.toPlainText()
        self.algo_list_text.setMinimumWidth(350)
        self.algo_list_text.setMinimumHeight(386)
        layout.addWidget(self.algo_list_text, 1, 1, 10, 1, alignment=Qt.AlignmentFlag.AlignTop)

        # заполняем текстовое поле
        selected_algo_text = ""
        for new_item in self.selected_algoritms_list:
            key = new_item["selected_key"]
            selected_opt1 = new_item["selected_opt1"]
            selected_opt2 = new_item["selected_opt2"]
            selected_opt3 = new_item["selected_opt3"]

            alg_name = self.data[key]
            selected_algo_text += f"{alg_name}"
            selected_algorithm = self.algorithm_fields[key]
            if len(self.algorithm_fields[key]) > 0:
                alg_opt1 = json.loads(selected_algorithm[0]['options'])
                opt1_text = alg_opt1[selected_opt1]
                selected_algo_text += f": {opt1_text}"
            if len(self.algorithm_fields[key]) > 1:
                alg_opt2 = json.loads(selected_algorithm[1]['options'])
                opt2_text = alg_opt2[selected_opt2]
                selected_algo_text += f", {opt2_text}"
            if len(self.algorithm_fields[key]) > 2:
                alg_opt3 = json.loads(selected_algorithm[2]['options'])
                opt3_text = alg_opt3[selected_opt3]
                selected_algo_text += f", {opt3_text}"

            selected_algo_text += f"\n"

        self.algo_list_text.setText("")
        self.algo_list_text.setText(selected_algo_text)     

        # Создаем кнопку для закрытия формы
        close_button = QPushButton("Select Algorithms", separation_dialog)
        close_button.setStyleSheet(button_style)  # Применяем стиль для кнопок
        close_button.clicked.connect(separation_dialog.accept)
        layout.addWidget(close_button,8,1)

        # Создаем кнопку для очистки алгоритмов
        clear_algo_button = QPushButton("Clear Algorithms", separation_dialog)
        clear_algo_button.setStyleSheet(button_style)  # Применяем стиль для кнопок
        clear_algo_button.clicked.connect(self.clear_algo)
        layout.addWidget(clear_algo_button, 9, 0, 2, 0)


        # Устанавливаем layout в диалоговое окно
        separation_dialog.setLayout(layout)

        # Отображаем диалоговое окно
        separation_dialog.exec()



    def clear_algo(self):
        self.selected_algoritms_list = []
        self.algo_list_text.setText("")



    def add_algoritm(self):
        # Получаем выбранный текст
        selected_item = self.type_combo_master.currentText()
        for key, value in self.data.items():
            if value == selected_item:
                separation_type = key
                break

        self.clear_styles()
        if not separation_type:  # Если тип сепарации не выбран
            self.type_combo_master.setStyleSheet(f"border: 2px solid red; {combo_style}")

        else:
            new_item = {}
            new_item["selected_key"] = key
            new_item["selected_opt1"] = self.selected_opt1
            new_item["selected_opt2"] = self.selected_opt2
            new_item["selected_opt3"] = self.selected_opt3
            self.selected_algoritms_list.append(new_item)

            # заполняем текстовое поле
            selected_algo_text = ""
            for new_item in self.selected_algoritms_list:
                key = new_item["selected_key"]
                selected_opt1 = new_item["selected_opt1"]
                selected_opt2 = new_item["selected_opt2"]
                selected_opt3 = new_item["selected_opt3"]

                alg_name = self.data[key]
                selected_algo_text += f"{alg_name}"
                selected_algorithm = self.algorithm_fields[key]
                if len(self.algorithm_fields[key]) > 0:
                    alg_opt1 = json.loads(selected_algorithm[0]['options'])
                    opt1_text = alg_opt1[selected_opt1]
                    selected_algo_text += f": {opt1_text}"
                if len(self.algorithm_fields[key]) > 1:
                    alg_opt2 = json.loads(selected_algorithm[1]['options'])
                    opt2_text = alg_opt2[selected_opt2]
                    selected_algo_text += f", {opt2_text}"
                if len(self.algorithm_fields[key]) > 2:
                    alg_opt3 = json.loads(selected_algorithm[2]['options'])
                    opt3_text = alg_opt3[selected_opt3]
                    selected_algo_text += f", {opt3_text}"

                selected_algo_text += f"\n"

            self.algo_list_text.setText("")
            self.algo_list_text.setText(selected_algo_text)            

    def on_selection_master_change(self, index):
        # Получаем выбранный текст
        selected_item = self.type_combo_master.currentText()

        # Ищем соответствующий ключ для выбранного значения
        for key, value in self.data.items():
            if value == selected_item:
                self.selected_key = key
                
                selected_algorithm = self.algorithm_fields[key]
                # очищаем все ComboBox в окне мастера
                self.option1_combo_master.clear()
                self.option2_combo_master.clear()
                self.option3_combo_master.clear()
                self.option1_label_master.setText("Additional Option 1")
                self.option2_label_master.setText("Additional Option 2")
                self.option3_label_master.setText("Additional Option 3")

                if len(self.algorithm_fields[key]) > 0:
                    self.option1_label_master.setText(f"Additional Option 1: {selected_algorithm[0]['text']}")
                    self.alg_opt1 = json.loads(selected_algorithm[0]['options'])
                    # Сортируем словарь по ключу
                    sorted_data = {k: v for k, v in sorted(self.alg_opt1.items())}
                    value = sorted_data.values()
                    # Добавляем элементы в комбобокс
                    self.option1_combo_master.addItems(value)

                if len(self.algorithm_fields[key]) > 1:
                    self.option2_label_master.setText(f"Additional Option 2: {selected_algorithm[1]['text']}")
                    self.alg_opt2 = json.loads(selected_algorithm[1]['options'])
                    # Сортируем словарь по ключу
                    sorted_data = {k: v for k, v in sorted(self.alg_opt2.items())}
                    value = sorted_data.values()
                    # Добавляем элементы в комбобокс
                    self.option2_combo_master.addItems(value)
               
                if len(self.algorithm_fields[key]) > 2:
                    self.option3_label_master.setText(f"Additional Option 3: {selected_algorithm[2]['text']}")
                    self.alg_opt3 = json.loads(selected_algorithm[2]['options'])
                    # Сортируем словарь по ключу
                    sorted_data = {k: v for k, v in sorted(self.alg_opt3.items())}
                    value = sorted_data.values()
                    # Добавляем элементы в комбобокс
                    self.option3_combo_master.addItems(value)

                break


    def on_change_master_option1(self, index):
        # Получаем выбранный текст
        selected_item = self.option1_combo_master.currentText()
        # Ищем соответствующий ключ для выбранного значения
        for key, value in self.alg_opt1.items():
            if value == selected_item:
                self.selected_opt1 = key
                break

    def on_change_master_option2(self, index):
        # Получаем выбранный текст
        selected_item = self.option2_combo_master.currentText()
        # Ищем соответствующий ключ для выбранного значения
        for key, value in self.alg_opt2.items():
            if value == selected_item:
                self.selected_opt2 = key
                break

    def on_change_master_option3(self, index):
        # Получаем выбранный текст
        selected_item = self.option3_combo_master.currentText()
        # Ищем соответствующий ключ для выбранного значения
        for key, value in self.alg_opt3.items():
            if value == selected_item:
                self.selected_opt3 = key
                break


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())
