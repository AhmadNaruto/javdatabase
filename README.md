# JAV Database 

for the firsttime

from jav.collector import Collector

data = jav.Collector('data.db') 
data.build_table('scheme.sql')

#how many conection per scraping

await data.run_scraper(fetch_worker=30)
'
