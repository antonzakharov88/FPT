import time
import os
from numpy import equal
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
        #options.add_argument('--headless')
        options.add_argument("disable-infobars")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox"); 
        options.add_experimental_option("prefs", preferences)        
        #self.browser = webdriver.Chrome('/usr/lib/chromium-browser/chromedriver', chrome_options=options) # for cloud
        self.browser = webdriver.Chrome(f'{dir}/chromedriver', chrome_options=options) # for desktop
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

        list_tds = [list_tds[i:i+7] for i in range(0, len(list_tds), 7)] 

        for item in soup.find("div", class_="dataTables_scrollBody").find_all('a'):
            href = f'https://itdashboard.gov{item.get("href")}'
            if href not in list_urls:    
                list_urls.append(href)
            
        df = pd.DataFrame(list_tds, columns=("uii", "Bureau", "Investment Title", "spending", "Type", "CIO Rating", "of Projects"))
        df.to_excel(f"./{title}.xlsx", sheet_name='data', index=False)
        self.df_dict = df.to_dict("index")
        
        
        for url in list_urls:
            self.browser.get(url)
            time.sleep(20)
            download_link = self.browser.find_element_by_xpath('//*[@id="business-case-pdf"]/a')
            download_link.click()
            time.sleep(10)
        

    def compare_results(self, title):
        pdf_files = glob(f'{os.path.abspath(os.curdir)}/*.pdf') # Looking for all pdf files

        # Creating a compare list with values from keys of data frame dict
        # updating the obtained dictionary with the keys "compare uii" and "compare Investment Title" whith default values

        compare_list = [value for key, value in self.df_dict.items()]
 
        for dict in compare_list:
                dict.update({"compare uii": "no match pdf uii", 
                            "compare Investment Title": "no match pdf Investment Title"})

        #---------------------------------------------------------------------------------------------------------------
        # read and extract data from pdf files
         
        for file in pdf_files:
            pdf = pdfquery.PDFQuery(file)
            pdf.load(0)

            #------------------------------------------------------------------------------------------------------------
            # Get a list of items (text) from the desired section of the pdf
            
            uii_list = pdf.pq('LTTextLineHorizontal:contains("Unique Investment Identifier (UII):")').text()
            name_list = pdf.pq('LTTextLineHorizontal:contains("Name of this Investment:")').text()

            #------------------------------------------------------------------------------------------------------------
            # Format these lists and get the necessary values 
            # Unique Investment Identifier (UII) and Name of this Investment

            uii_list = uii_list.split(":")
            uii = uii_list[1][1:]
            name_list = name_list.split(":")
            name_of_investment = name_list[1][1:]
            pdf_name = file[-17:]
            
            #------------------------------------------------------------------------------------------------------------           
            # compare the values obtained from the pdf file with the values from the data, 
            # and update the current dictionary if the comparison is successful

            for dict in compare_list:    
                if dict.get("uii") == uii:
                    dict.update({"compare uii": f"{pdf_name} uii match current uii"})
                if dict.get("Investment Title") == name_of_investment:
                    dict.update(
                        {"compare Investment Title": f"{pdf_name} name of investment match current Investment Title"}
                        )

        #-----------------------------------------------------------------------------------------------------------------    
        # Write the results in compare.xlsx         
        df = pd.DataFrame(compare_list)
        df.to_excel(f"{os.path.abspath(os.curdir)}/compare.xlsx", sheet_name='Test results', index=False)
        