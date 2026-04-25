import logging
logging.basicConfig(level=logging.INFO)
from scraper.arabam import ArabamScraper
s = ArabamScraper()
html = s.fetch("https://www.arabam.com/ikinci-el?searchText=BMW+320i&sort=price&yearMin=2022&yearMax=2022")
print("arabam:", "OK len=" + str(len(html)) if html else "FAILED 403")
