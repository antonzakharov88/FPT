"""Template robot with Python."""
from bot import Bot


if __name__ == "__main__":
    url = 'https://itdashboard.gov/'
    title = 'Department of Agriculture'
    my_bot = Bot(url, "Agencies")
    my_bot.scrap()
    my_bot.download(title) 
    my_bot.close_browser()
    my_bot.compare_results(title)