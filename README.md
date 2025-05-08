# Project: GUI for Interaction with MVSep.com Website

This document serves as a user guide for utilizing the graphical user interface (GUI) specifically designed for interacting with the MVSep.com website. The interface allows users to upload files, choose processing algorithms, and track operation statuses. We will explore the project structure, its core components, and steps for configuration and launching the application.

## Overview of Application

The application is built using the PyQt6 framework, which is widely used for developing desktop applications with graphical interfaces. Its primary goal is to simplify the process of uploading audio files and configuring various sound-processing algorithms. This significantly enhances user interaction with MVSep.com by enabling efficient handling of large datasets and faster results delivery.

## Key Features

1. **File Upload:**
   Users can select one or multiple audio files for further processing. Supported formats include MP3 and WAV. Users have the ability to directly drag and drop files into the application window or use their operating system's standard file selection dialog.

2. **Algorithm Selection:**
   A convenient wizard provides options for selecting different sound signal processing algorithms. Available choices include instrument separation, noise reduction, and quality enhancement. Each algorithm comes with advanced settings that allow customization tailored to specific needs.

3. **Multi-algorithm Processing:**
   The interface supports simultaneous processing of a single file through multiple algorithms, ensuring flexibility and ease when working with diverse scenarios involving sound signal processing.

4. **Process Monitoring:**
   Operation statuses are displayed in real-time via a dedicated table. Users can monitor each stage of every file being processed, starting from initial loading up until final completion.

5. **Thread Utilization (QThread):**
   The application leverages multithreading, providing smooth performance even during heavy processing tasks. Each thread tracks individual task progress, updating state information within the status table dynamically.

## Installation and Launch

To launch the application, simply execute the executable file `MVSepApp.exe`. This eliminates the need for installing all required dependencies onto the user's device.

## Application Architecture

The project consists of several essential components:

- **MainWindow:** The main application window implemented by the `MainWindow` class.
- **SepThread:** A thread class responsible for monitoring process states.
- **DragButton:** Button supporting drag-and-drop functionality for file transfers.
- **Database:** An SQLite database storing operational history and current assignments.

### Class MainWindow
The core component of the application contains widgets such as tables, buttons for file selection, and algorithm setup. It implements logic for managing program state and visualizing user actions.

### Class SepThread
A subclass of `QThread` designed for tracking and updating process statuses. It polls servers periodically and updates both the database and user interface accordingly.

### Basic Logic of the Application
Upon startup, the application establishes a connection to an SQLite database where tasks and log entries are stored. When a user selects a file and clicks “Create Separation,” a record is created in the database, initiating the file processing workflow.

## Implementation Highlights

### Use of Threads
One significant feature of this application is its utilization of threads (`QThread`) for parallel file processing. This ensures seamless operation even under extended processing operations.

Each thread regularly queries server-side task statuses and updates corresponding rows in the status table, allowing users to view real-time progress across all active processes.

## Data Storage
All completed operations are recorded in a local SQLite database. This storage retains critical details including:

- Unique task identifier.
- Name of the processed file.
- Selected processing type.
- Current task status.
- Additional metadata related to status changes.

This architecture helps users manage ongoing tasks efficiently and review past activities easily.

## Graphical User Interface
The GUI is developed using the PyQt6 libraries. Elements of the user interface include:

- Input field for entering a user token (with a link provided below it for authenticated users who haven't obtained a token yet).
- Table displaying the current status of tasks.
- Buttons for file selection and initiation of processing.
- Wizard for choosing algorithms and setting them up.
- Directory selector button specifying output directories for saved separations.
- Display of already-selected files and algorithms to enhance usability.
- Clearing options for removing previously chosen files or algorithms when needed.




# Проект: GUI для взаимодействия с сайтом MVSep.com
Этот документ представляет собой руководство по использованию графического интерфейса пользователя (GUI), разработанного специально для взаимодействия с веб-сайтом MVSep.com. Данный интерфейс позволяет пользователям загружать файлы, выбирать алгоритмы обработки и отслеживать статус выполняемых операций. Мы рассмотрим структуру проекта, ключевые компоненты и шаги по настройке и запуску приложения.

## Обзор Приложения
Приложение создано с использованием фреймворка PyQt6, популярного инструмента для разработки настольных приложений с графическим интерфейсом. Основной целью является упрощение процесса загрузки аудиофайлов и настройки различных алгоритмов обработки звука. Это значительно облегчает взаимодействие пользователей с сайтом MVSep.com, позволяя обрабатывать большие объемы данных и получать результаты быстрее и удобнее.

## Основные Функции
1. Загрузка Файлов:
Пользователи могут выбрать один или несколько аудиофайлов для последующей обработки. Поддерживаются форматы MP3 и WAV. Пользователь имеет возможность перетаскивать файлы непосредственно в область окна приложения или воспользоваться стандартным окном открытия файлов операционной системы.

2. Выбор Алгоритмов:
Предоставляется удобный мастер, позволяющий выбрать различные алгоритмы обработки звукового сигнала. Доступны разные варианты, такие как разделение инструментов, удаление шума и повышение качества записи. Для каждого алгоритма предусмотрены расширенные настройки, позволяющие оптимизировать обработку под конкретные нужды пользователя.

3. Chain-обработка множеством алгоритмов:
Интерфейс поддерживает одновременную обработку одного файла несколькими алгоритмами, что обеспечивает гибкость и удобство в работе с различными сценариями обработки звуковых сигналов.

4. Мониторинг Процессов:
Отображение статуса каждой операции выполняется в режиме реального времени через специальную таблицу. Пользователь может видеть, какой этап проходит каждый файл, начиная от начальной загрузки и заканчивая финальной стадией завершения обработки.

5. Использование Тредов (QThread):
Приложение активно использует многопоточность, обеспечивая плавную работу даже при обработке большого количества файлов одновременно. Каждый поток отслеживает состояние отдельных заданий, обновляя данные в таблице состояния в реальном времени.

## Установка и Запуск
Чтобы запустить приложение, требуется запустить исполняемый файл - MVSepApp.exe. Это избавляет пользователя от необходимости устанавливать все требуемые приложением зависимости на свое устройство.

## Архитектура Приложения
Проект состоит из нескольких ключевых компонентов:

* MainWindow — основное окно приложения, реализованное классом MainWindow.
* SepThread — класс потока, обеспечивающий мониторинг состояний процессов.
* DragButton — кнопка, поддерживающая перетаскивание файлов («drag-and-drop»).
* Database — база данных SQLite для хранения истории операций и текущих заданий.

### Класс MainWindow
Основной компонент приложения, содержащий виджет таблицы, кнопки для выбора файлов и настроек алгоритмов. Этот класс реализует всю логику управления состоянием программы и визуализации действий пользователя.

### Класс SepThread
Класс, наследующий от QThread, предназначенный для мониторинга и обновления статуса процессов. Реализует цикл опроса серверов и обновление базы данных и интерфейса пользователя.

### Базовая логика работы приложения
При старте программа создает соединение с базой данных SQLite, где хранятся задания и логи изменений. Когда пользователь выбирает файл и нажимает кнопку «Создать разделение», создается запись в базе данных, и начинается процесс обработки файла.

## Особенности Реализации
### Использование Threads
Важнейшей особенностью данного приложения является использование потоков (QThread) для параллельной обработки файлов. Благодаря этому обеспечивается плавная работа интерфейса даже при выполнении длительных операций.

Каждый поток периодически запрашивает у сервера статус текущего задания и обновляет соответствующую строку в таблице состояний. Таким образом, пользователь видит прогресс обработки всех файлов в реальном времени.

## Хранение Данных
Все выполненные операции сохраняются в локальной базе данных SQLite. База хранит следующую информацию:

## Уникальный идентификатор задания.
* Имя обрабатываемого файла.
* Тип выбранной обработки.
* Текущий статус задания.
* Дополнительные метаданные (лог изменения статуса).
Эта структура помогает пользователю легко управлять заданиями и просматривать историю выполненных операций.

## Графический Интерфейс
Графический интерфейс выполнен с использованием библиотек PyQt6. Элементы UI включают:

* Окно для ввода пользовательского токена, если пользователь не получил токен, под этим окном есть ссылка на получение токена для аутентифицированных пользователей.
* Таблицу для отображения текущего состояния заданий.
* Кнопки для выбора файлов и начала обработки.
* Мастер выбора алгоритмов и их настроек.
* Кнопка для выбора директории, в которую будут сохраняться все выполненные разделения.
* Отображение уже выбранных файлов и алгоритмов, для обеспечения лучшего пользовательского опыта.
* Очистку всех выбранных файлов или алгоритмов при необходимости.