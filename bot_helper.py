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
    img_alt = comic_data['alt']
    title = comic_data['title']
    img_name = os.path.join('images', f'{img_number}.png')
  
    return {"img_alt": img_alt, "title": title, "img_name": img_name, "img_content":img_response.content}



