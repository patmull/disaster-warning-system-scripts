import urllib.request

from bs4 import BeautifulSoup

url = 'http://www.hygpraha.cz/'

hygpraha = urllib.request.urlopen(url)

page_soup = BeautifulSoup(hygpraha, 'html.parser')

divs_vypis_items = page_soup.find_all('div', {'class': 'vypis-item'})

for divs_vypis_item in divs_vypis_items:
    h3_vypis_items = divs_vypis_item.findAll('h3')
    p_vypis_item = divs_vypis_item.findAll('p')

    for h3_vypis_item in h3_vypis_items:
        a_vypis_item = h3_vypis_item.findAll('a')
        a_vypis_item_href = h3_vypis_item.find('a')['href']

        print('H3:')
        if a_vypis_item:
            print(a_vypis_item[0].text)
            print('A HREF:')
            print('http://www.hygpraha.cz' + a_vypis_item_href)
    
        print('P:')
        if p_vypis_item:
            print(p_vypis_item[1].text)
