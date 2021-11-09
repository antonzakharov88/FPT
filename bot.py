import time
import os
import pdfquery
import pandas as pd

from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from glob import glob


class Bot():
    
    def __init__(self, url, page_name):
        self.url = url
        self.page_name = page_name
        dir = os.path.abspath(os.curdir)
        download_dir = dir
        preferences = {"download.default_directory": download_dir ,
                   "directory_upgrade": True,
                   "safebrowsing.enabled": True }
                
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument("disable-infobars")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox"); 
        options.add_experimental_option("prefs", preferences)        
        self.browser = webdriver.Chrome('/usr/lib/chromium-browser/chromedriver', chrome_options=options) # for cloud
        #self.browser = webdriver.Chrome(f'{dir}/chromedriver', chrome_options=options) # for desktop
        self.accept_next_alert = True


    def close_browser(self):
        self.browser.close()
        self.browser.quit()
    

    def scrap(self):
        self.browser.get(self.url)
        time.sleep(3)
        button = self.browser.find_element_by_xpath('//*[@id="node-23"]/div/div/div/div/div/div/div/a')
        button.click()
        content = self.browser.page_source

        soup = BeautifulSoup(content, "lxml")

        organizations = []
        for org in soup.find("div", id="agency-tiles-widget").find_all("span", class_="h4 w200"):
            organizations.append(org.text)

        spending = []
        for spend in soup.find("div", id="agency-tiles-widget").find_all("span", class_="h1 w900"):
            spending.append(spend.text)
        
        list_urls = []
        all_a = soup.find("div", id="agency-tiles-widget").find_all("a")
        for item in all_a:
            href = f'{self.url}{item.get("href")}'
            if href not in list_urls:    
                list_urls.append(href)

        self.table = dict(zip(organizations, list_urls))

        df = pd.DataFrame({"name": organizations, "spending": spending})
        df.to_excel(f"./{self.page_name}.xlsx", sheet_name='Agencies', index=False)
        time.sleep(2)


    def download(self, title):
        url = self.table[title]
        self.browser.get(url)
        time.sleep(10)

        select_button = Select(self.browser.find_element_by_name(name="investments-table-object_length"))
        select_button.select_by_visible_text('All')
        time.sleep(10)
        list_tds = []
        list_urls = []
        filter_value = ["Filter by BureauAllAgricultural Marketing ServiceAgricultural Research ServiceAnimal and Plant Health Inspection ServiceBuildings and FacilitiesDepartment of AgricultureDepartmental ManagementEconomic Research ServiceExecutive OperationsFarm Production and Conservation Business CenterFarm Service AgencyFood and Nutrition ServiceFood Safety and Inspection ServiceForeign Agricultural ServiceForest ServiceGrain Inspection, Packers and Stockyards AdministrationHazardous Materials ManagementNational Agricultural Statistics ServiceNational Appeals DivisionNational Institute of Food and AgricultureNatural Resources Conservation ServiceOffice of Chief EconomistOffice of Chief Financial OfficerOffice of Chief Information OfficerOffice of Civil RightsOffice of CommunicationsOffice of Inspector GeneralOffice of the General CounselOffice of the SecretaryRisk Management AgencyRural Business_Cooperative ServiceRural DevelopmentRural Housing ServiceRural Utilities Service",
        "Filter by TypeAllMajor ITNon-major ITIT MigrationFunding TransferStandard IT Infrastructure", ""]
        html = self.browser.execute_script("return document.documentElement.outerHTML")
        soup = BeautifulSoup(html, "lxml")
        
        for td in soup.find("div", class_="dataTables_scrollBody").find_all("td"):
            if td.text not in filter_value:
                list_tds.append(td.text) 
        f = lambda A, n=7: [A[i:i+n] for i in range(0, len(A), n)]
        list_tds = f(list_tds) 

        for item in soup.find("div", class_="dataTables_scrollBody").find_all('a'):
            href = f'https://itdashboard.gov{item.get("href")}'
            if href not in list_urls:    
                list_urls.append(href)
            
        df = pd.DataFrame(list_tds, columns=("ull", "Bureau", "Investment Title", "spending", "Type", "CIO Rating", "of Projects"))
        df.to_excel(f"./{title}.xlsx", sheet_name='data', index=False)

        for url in list_urls:
            self.browser.get(url)
            time.sleep(20)
            download_link = self.browser.find_element_by_xpath('//*[@id="business-case-pdf"]/a')
            download_link.click()
            time.sleep(10)
    

    def compare_results(self, title):
        pdf_files = glob(f'{os.path.abspath(os.curdir)}/*.pdf') # ищем все pdf файлы

        # создаем словарь с ключами, в который в дальнейшем добавим значения

        compare_dict = {"ull": [], "Investment Title": [], "status": []}

        #---------------------------------------------------------------------------------------------------------------
        # читаем и извлекаем необходимые данные из pdf файлов
         
        for file in pdf_files:
            pdf = pdfquery.PDFQuery(file)
            pdf.load(0)
            label = pdf.pq(':contains("1. Name of this Investment:")')

            #------------------------------------------------------------------------------------------------------------
            # Получаем список элементов(текст) из нужного раздела pdf
            
            uii_list = pdf.pq('LTTextLineHorizontal:contains("Unique Investment Identifier (UII):")').text()
            name_list = pdf.pq('LTTextLineHorizontal:contains("Name of this Investment:")').text()

            #------------------------------------------------------------------------------------------------------------
            # Фоматируем полученные списки и получаем необходимые значения 
            # Unique Investment Identifier (UII) и Name of this Investment

            uii_list = uii_list.split(":")
            uii = uii_list[1][1:]
            name_list = name_list.split(":")
            name_of_investment = name_list[1][1:]
            
            #------------------------------------------------------------------------------------------------------------            
            # Создаем словарь и записываем в него значения Unique Investment Identifier (UII) и Name of this Investment 
            # с ключами: "ull" и "Investment Title" соответственно

            tmp_dict = {"ull": uii, "Investment Title": name_of_investment}
            
            #------------------------------------------------------------------------------------------------------------           
            # Извлекаем из нужного xlsx файла колонки uii и Investment Title и записываем в словарь с аналогичными ключами
            # Получаем лист словарей "data_list"

            with pd.ExcelFile(f"./{title}.xlsx") as reader:
                sheet = pd.read_excel(reader, sheet_name='data', usecols=["ull", "Investment Title"])
                data_list = sheet.to_dict(orient='records')

            #------------------------------------------------------------------------------------------------------------
            # Сравниваем полученный словарь(tmp_dict) из pdf со словарями из xlsx файла
            # если он пристутсвует в списке словарей из xlsx файла, обновляем текущий словарь tmp_dict 
            # значением "match" с ключом "status"

                if tmp_dict in data_list:
                    tmp_dict.update({"status": "match"})        
                else:
                    tmp_dict.update({"status": "mismatch"})

            #------------------------------------------------------------------------------------------------------------
            # добавляем значения из словаря tmp_dict по ключам в словарь сравнения "compare_dict", который создали вначале

            for key in tmp_dict.keys():
                compare_dict[key].append(tmp_dict[key])
            
        #------------------------------------------------------------------------------------------------------------
        # Записываем результаты проверки в compare.xlsx         
        df = pd.DataFrame(compare_dict)
        df.to_excel(f"{os.path.abspath(os.curdir)}/compare.xlsx", sheet_name='Test results', index=False)
        