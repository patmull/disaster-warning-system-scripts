import urllib.request
import re

from bs4 import BeautifulSoup

url = 'https://koronavirus.mzcr.cz/category/mimoradna-opatreni-a-doporuceni/'

hygpraha = urllib.request.urlopen(url)

page_soup = BeautifulSoup(hygpraha, 'html.parser')

articles = page_soup.find_all('article')

for article in articles:
    p_summary = article.find_all('p', {'class': 'summary'})
    ases = article.findAll('a')

    for a in ases:

        h2 = a.find_all('h2')

        if h2:
            print('H2:')
            print(h2[0].text)
            a_href = a['href']
            print('A HREF:')
            print(a_href)
            print('P:')
            p = re.sub(r'\n\s*\n', r'\n\n', p_summary[0].text.strip(), flags=re.M)
            print(p)

"""
print('H3:')
        if a_vypis_item:
            print(a_vypis_item[0].text)
            print('A HREF:')
            print('http://www.hygpraha.cz' + a_vypis_item_href)
    
        print('P:')
        if p_vypis_item:
            print(p_vypis_item[1].text)
"""
