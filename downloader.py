import requests
import os
import argparse

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
    return comic_data


def download_image(comic_data,num):
    img_link = comic_data['img']
    img_response = requests.get(img_link)
    img_response.raise_for_status()
    img_name = os.path.join('images', f'{num}.png')
    img_alt = comic_data['alt']
    with open(img_name, 'wb') as img_file:
        img_file.write(img_response.content)
    print(f'Изображение {num} сохранено в {img_name}.')
    return img_alt

def load_comics(max_load=50):
    images_count = get_total_comics()
    for num in range(1, images_count):
        comic = get_comic(num)
        download_image(comic_data=comic, num=num)
        if num == max_load:
            break

def main():
    parser = argparse.ArgumentParser(
        prog='Загрузчик ищображений',
        description='Загружает изображения из комиксов',
    )
    parser.add_argument('-c', '--count', help='Максимальное количество выгруженных изображений', default=5, type=int)
    args = parser.parse_args()
    load_comics(args.count)


if __name__ == "__main__":
    main()


