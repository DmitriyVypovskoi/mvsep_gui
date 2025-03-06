import requests


def get_separation_types():
    # URL для запроса
    api_url = 'https://mvsep.com/api/app/algorithms'

    # Делаем GET-запрос
    response = requests.get(api_url)

    # Проверяем статус-код ответа
    if response.status_code == 200:
        # Парсим ответ в JSON
        data = response.json()
        result = {}  # Создаем новый словарь для сохранения данных по render_id

        # Проверка структуры данных (для отладки)
        if isinstance(data, list):  # Проверяем, что data - это список
            for algorithm in data:
                if isinstance(algorithm, dict):  # Проверяем, что каждый элемент - это словарь
                    render_id = algorithm.get('render_id', 'N/A')
                    name = algorithm.get('name', 'N/A')
                    algorithm_group_id = algorithm.get('algorithm_group_id', 'N/A')

                    # Дополнительные поля
                    algorithm_fields = algorithm.get('algorithm_fields', [])
                    for field in algorithm_fields:
                        if isinstance(field, dict):
                            field_name = field.get('name', 'N/A')
                            field_text = field.get('text', 'N/A')
                            field_options = field.get('options', 'N/A')
                            # Печать дополнительных полей (можно удалить, если не нужно)
                            print(f"\tField Name: {field_name}, Field Text: {field_text}, Options: {field_options}")

                    # Описания алгоритма
                    algorithm_descriptions = algorithm.get('algorithm_descriptions', [])
                    for description in algorithm_descriptions:
                        if isinstance(description, dict):
                            short_desc = description.get('short_description', 'N/A')
                            lang = description.get('lang', 'N/A')
                            # Печать описания алгоритма (можно удалить, если не нужно)
                            print(f"\tShort Description: {short_desc}, Language: {lang}")

                    # Сохраняем данные в result по render_id
                    result[render_id] = name
                    # Печать данных для примера
                    print(f"{render_id}: {name}, Group ID: {algorithm_group_id}")

        else:
            print(f"Unexpected top-level data format: {data}")

        # Возвращаем результат (можно использовать для дальнейшей обработки)
        print(result)
        return result
    else:
        print(f"Request failed with status code: {response.status_code}")
