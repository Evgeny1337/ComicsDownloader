import requests
from downloader import get_total_comics,get_comic,download_about

def main():
    images_count = get_total_comics()
    for num in range(1,images_count):
        comic = get_comic(num)
        print(comic)
        # print(download_about(comic,num))

    


if __name__ == "__main__":
    main()