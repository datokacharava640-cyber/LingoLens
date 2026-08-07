import time
from time import sleep

def start_background_listener():
    """ფონური სერვისი Hotword 'LingoLens'-ის მოსასმენად"""
    while True:
        # ფონური რეჟიმის მოსმენის ციკლი
        sleep(2)

if __name__ == '__main__':
    start_background_listener()
