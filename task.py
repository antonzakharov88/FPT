"""Template robot with Python."""
from bot import Bot

def minimal_task():
    print("Done.")


if __name__ == "__main__":
    url = 'https://itdashboard.gov/'
    my_bot = Bot(url, "Agencies")
    my_bot.scrap()
    my_bot.download('Department of Agriculture') 
