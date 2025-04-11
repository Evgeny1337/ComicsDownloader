import requests
import os

def get_comic(img_url):
    response = requests.get(img_url)
    response.raise_for_status()
    comic_data = response.json()
    return comic_data


def download_image(comic_data):
    img_link = comic_data['img']
    img_response = requests.get(img_link)
    img_response.raise_for_status()
    img_number = comic_data['num']
    img_name = os.path.join('images', f'{img_number}.png')
    img_alt = comic_data['alt']
    title = comic_data['title']
    os.makedirs('images', exist_ok=True)
    with open(img_name, 'wb') as img_file:
        img_file.write(img_response.content)
    print(f'Изображение {img_number} сохранено в {img_name}.')
    return {"img_alt": img_alt, "title": title, "img_name": img_name}

