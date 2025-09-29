from selenium import webdriver as wd
from selenium.webdriver.common.by import By
from datetime import datetime, timedelta, timezone
from src.OutputMessage import OutputMessage


class WebScraper:
    def __init__(self, time_cutoff: datetime):
        self.links = []
        self.vacancies = []
        self.cutoff = time_cutoff


        self.driver = wd.Chrome()
        self._get_page()
        self._parse_vacancies()
        self.driver.quit()


    def _get_page(self):
       raise NotImplementedError("Use DerivedClass") 

    def _parse_vacancies(self):
       raise NotImplementedError("Use DerivedClass") 
    
    def get_vacancies(self):
        return self.vacancies

class HitMakerScraper(WebScraper):
    def __init__(self, time_cutoff):
        self.link = "https://hitmarker.net/jobs?page=3"
        super().__init__(time_cutoff)

    def _get_page(self):
        self.driver.get(self.link)
        div = self.driver.find_element(By.CLASS_NAME, "space-y-3")
        elements = div.find_elements(By.XPATH, ".//a")

        links = []
        for e in elements:
            span = e.find_element(By.CSS_SELECTOR, "span[data-datetime]")
            date_str = span.get_attribute("data-datetime")
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            if (dt > self.cutoff):
                self.links.append(e.get_attribute("href"))


    def _parse_vacancies(self):
        for l in self.links:
            self.driver.get(l)
            div = self.driver.find_element(By.CLASS_NAME, "prose")
            self.vacancies.append(OutputMessage(div.text, l)) 
        
        print(*self.vacancies)
    



