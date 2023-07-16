from datetime import datetime
import requests
from user_data import VK_TOKEN, YANDEX_TOKEN, user_id
from progress.bar import IncrementalBar
import json


class APIVk:
    BASE_URL = 'https://api.vk.com/method'

    def __init__(self, token, user_id):
        self.token = token
        self.user_id = user_id

    @staticmethod
    def get_params():
        return {
            'access_token': VK_TOKEN,
            'v': '5.131'
        }

    def get_profile_photos(self):
        params = self.get_params()
        count = 5
        params.update({'owner_id': self.user_id, 'album_id': 'profile', 'rev': 1, 'extended': 1, 'count': count})
        response = requests.get(f'{self.BASE_URL}/photos.get', params=params).json()
        return response

    def add_photos_to_list(self):
        response = self.get_profile_photos()
        photos = []
        for photo in response['response']['items']:
            max_size = 0
            photo_url = ''
            for size in photo['sizes']:
                if size["height"] >= max_size:
                    max_size = size["height"]
                    photo_url = size['url']
                    size_to_json = size['type']
            if max_size > 0:
                date_photo = datetime.fromtimestamp(photo['date']).strftime('%Y-%m-%d')
                photos.append(
                    {'id': photo['id'], 'likes': photo['likes']['count'], 'url': photo_url, 'date': date_photo,
                     'size': size_to_json})
        res = self._make_json(photos)
        return res

    @staticmethod
    def _make_json(photos):
        file_names = []
        result = []
        for photo in photos:
            file_name = f"{str(photo['likes'])}.jpg"
            if file_name in file_names:
                file_name = (f"{str(photo['likes'])}"
                             f"{str(photo['date'])}".jpg
                             )
            file_names.append(file_name)
            items = {
                'file_name': file_name,
                'size': photo['size'],
                'url': photo['url']
            }
            result.append(items)
        with open("history.json", "w", encoding="utf-8") as file:
            json.dump(result, file)
        return result


class YandexUploader:
    def __init__(self, token):
        self.token = token

    def create_folder(self, folder_name):
        headers = {'Authorization': f'OAuth {self.token}'}
        url = 'https://cloud-api.yandex.net/v1/disk/resources'
        params = {"path": folder_name}
        result = requests.put(f'{url}', headers=headers, params=params)
        result.raise_for_status()
        if result.status_code == 201:
            return folder_name
        else:
            print(f"Ошибка при создании папки! = {result.status_code}")

    def upload_file(self, file, folder):
        file_name = folder + '/' + file['file_name']
        headers = {'Authorization': self.token}
        url = 'https://cloud-api.yandex.net/v1/disk/resources/upload'
        params = {
            'url': file['url'],
            'path': file_name,
            'overwrite': 'true'
        }
        res = requests.post(url=url, headers=headers, params=params)
        res.raise_for_status()
        return res

    def upload_photos(self, files):
        folder = self.create_folder("netology")
        responses = []
        i = 0
        bar = IncrementalBar('Загрузка фотографий на яндекс диск', max=len(files))
        for file in files:
            responses.append(self.upload_file(file, folder))
            if responses[i].status_code == 202:
                print(f'Файл {file["file_name"]} загружен')
            else:
                print(responses[i])
            i += 1
            bar.next()
        bar.finish()


if __name__ == '__main__':
    vk = APIVk(VK_TOKEN, user_id)
    vk.get_profile_photos()
    files = vk.add_photos_to_list()
    ya = YandexUploader(YANDEX_TOKEN)
    ya.upload_photos(files)
