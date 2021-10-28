"""Template robot with Python."""
from bot import Bot


if __name__ == "__main__":
    url = 'https://itdashboard.gov/'
    my_bot = Bot(url, "Agencies")
    my_bot.scrap()
    my_bot.download('Department of Agriculture') 
    my_bot.close_browser()