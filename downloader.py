import requests
import os


def get_total_comics():
    response = requests.get('https://xkcd.com/info.0.json')
    response.raise_for_status()
    data = response.json()
    return data['num']

def get_comic(num):
    img_url = f'https://xkcd.com/{num}/info.0.json'
    response = requests.get(img_url)
    response.raise_for_status()
    comic_data = response.json()
    # img_link = comic_data['img']
    # img_response = requests.get(img_link)
    # img_response.raise_for_status()
    return comic_data


def download_image(img_response,num):
    img_name = os.path.join('images', f'{num}.png')
    with open(img_name, 'wb') as img_file:
        img_file.write(img_response.content)
    print(f'Изображение {num} сохранено в {img_name}.')

def download_about(img_response,num):
    return "{} - {}".format(num,img_response['alt'])
