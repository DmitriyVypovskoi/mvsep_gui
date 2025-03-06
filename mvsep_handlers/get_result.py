import os
import json
import requests


def download_file(url, filename, save_path):
    """
    Download the file from the specified URL and save it in the specified path.
    """
    response = requests.get(url)

    if response.status_code == 200:
        # Ensure the directory exists
        if not os.path.exists(save_path):
            os.makedirs(save_path)

        file_path = os.path.join(save_path, filename)

        # Save the content of the response to the file
        with open(file_path, 'wb') as f:
            f.write(response.content)
        return f"File '{filename}' uploaded successfully!"
    else:
        print(f"There was an error loading the file '{filename}'. Status code: {response.status_code}.")


def get_result(hash, save_path):
    success, data = check_result(hash)
    if success:
        try:
            files = data['data']['files']
        except KeyError:
            print("The separation is not ready yet.")
            return ""
        text = ""
        for file_info in files:
            url = file_info['url'].replace('\\/', '/')  # Correct slashes
            filename = file_info['download']  # File name for saving
            text += f'{download_file(url, filename, save_path)}\n'
        return text
    else:
        print("An error occurred while retrieving file data.")

def check_result(hash):
    params = {'hash': hash}
    response = requests.get('https://mvsep.com/api/separation/get', params=params)
    data = json.loads(response.content.decode('utf-8'))

    return data['success'], data
