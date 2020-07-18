import ssl
import urllib.request
import xml.etree.ElementTree as ET
from geopy.geocoders import Nominatim

namespace = {"geo": "http://www.w3.org/2003/01/geo/",
         "emsc": "https://www.emsc-csem.org"}

url = 'https://www.emsc-csem.org/service/rss/rss.php?filter=yes&start_date=2020-02-01&min_mag=2.5&region=CZECH+REPUBLIC&min_intens=0&max_intens=8&distance=true'

ssl._create_default_https_context = ssl._create_unverified_context
ctx = ssl._create_unverified_context()

# filter with > 2.5 earthquake magnitudo
emcs_czech = urllib.request.urlopen(url, context=ctx)

tree = ET.parse(emcs_czech)

root = tree.getroot()

print(root[0].findall('title'))

for item in tree.findall('.//channel/item'):
    message_string = ''

    latitude = item.findall("geo:lat", namespace)[0].text
    longitude = item.findall('geo:long',namespace)[0].text
    magnitude = item.findall('emsc:magnitude',namespace)[0].text

    distance_list = ''

    for distance in item.findall('distance'):
        distance_list = distance.findall('city')[0].text +  distance.findall('city')[1].text + distance.findall('city')[2].text
        distance_list_string = ''.join(str(distance_list_item) for distance_list_item in distance_list)

    magnitude_int = float(list(filter(str.isdigit, magnitude))[0])

    text_type = ''

    if(magnitude_int == 2.0):
        alert_type = 'INFO'
        text_type = 'Velmi slabé zemětřesení'
        intensity_info = 'Zemětřesení by mělo být rozpoznatelné hlavně v horních patrech budov citlivými lidmi.'
    elif(magnitude_int == 3.0):
        alert_type = 'INFO'
        text_type = 'Slabé zemětřesení'
        intensity_info = 'Zemětřesení může způsobi vibrace, mohou se  pohybovat lustry. Intenzita by měla být ' \
                         'srovnatelná s vibracemi způsobenými projíždějícím těžkým nákladním automobilem.'
    elif (magnitude_int == 4.0):
        alert_type = 'VAROVÁNÍ'
        text_type = 'UPOZORNĚNÍ!!! Mírně silné'
        intensity_info = 'UPOZORNĚNÍ!!! Zemětřesení ' \
                         'může způsobit praskání oken, poškození omítek a zdí!' \
                         'Mírnější průběh může způsobit drnčení oken, cinkot příborů a nádobí.'
    elif (magnitude_int == 5.0):
        alert_type = 'VAROVÁNÍ'
        text_type = '!!!UPOZORNĚNÍ!!! SILNÉ ZEMĚTŘESENÍ!!!'
        intensity_info = '!!!UPOZORNĚNÍ!!! DRŽTE SE V OBLASTI ZEMĚTŘESENÍ DÁLE OD BUDOV, OKEN NEBO NÁBYTKU.' \
                         ' Zemětřesení může způsobit padání těžších předmětů, ' \
                         'praskání zdí, omítek! Možná ztížená chůze, rozbíjení nádobí a jiných předmětů.'
    elif (magnitude_int == 6.0):
        alert_type = 'VAROVÁNÍ'
        text_type = '!!!UPOZORNĚNÍ!!! VELMI SILNÉ AŽ DESTRUKTIVNÍ ZEMĚTŘESENÍ!!!'
        intensity_info = '!!!UPOZORNĚNÍ!!! DRŽTE SE DÁL OD OKEN, NÁBYTKU, POKUD JSTE VENKU, BUDOV A ' \
                         'CHRAŇTE SI HLAVU!!! ' \
                         'Zemětřesení může způsobit trhliny ve zdech, padání nábytku a ' \
                         'padání komínů. Může způsobit poškození budov.'
    elif (magnitude_int > 7.0):
        alert_type = 'VAROVÁNÍ'
        text_type = '!!!UPOZORNĚNÍ!!! NIČIVÉ ZEMĚTŘESENÍ'
        intensity_info = '!!!UPOZORNĚNÍ!!! SCHOVEJTE SE POD STŮL!!! DRŽTE SE DÁL OD OKEN, NÁBYTKU, POKUD JSTE VENKU,' \
                         'DRŽTE SE DÁL OD BUDOV A ' \
                         'CHRAŇTE SI HLAVU!!! ' \
                         'Zemětřesení může způsobit padání částí budov, vážné poškození ve zdech a trhliny v půde.'

    title = 'EMSC: ' + text_type + " magnitudy " + magnitude
    message_string += alert_type + ' | ' + 'EMSC: ' + text_type + " magnitudy " + magnitude
    geolocator = Nominatim(user_agent="Varovny_system_CR")
    location_string = latitude + ", " + longitude
    location = geolocator.reverse(location_string, language='cs')
    address = location.raw['address']
    if address.get('city') is not None:
        area = address.get('city') + ", " + address.get('suburb')
        message_string += ", " + area
        title += ", " + area
    else:
        area = address.get('suburb')
        message_string += ", " + area
        title += ", " + area

    time = item.findall('emsc:time',namespace)[0].text
    link_emsc = item.findall('link')[0].text
    message_string += ", " + time
    title += ", " + time

    earthquake_time = item.findall('emsc:time', namespace)[0].text
    link_emsc = item.findall('link')[0].text
    message_string += ", " + earthquake_time
    title += ", " + earthquake_time

    excerpt = intensity_info + ' Další podrobnosti o zemětřesení najdete na <a href=\"' + link_emsc + '\">webu Evropsko-středozemního seismologického centra</a>'

    body = 'Zemětřesení bylo detekováno v oblasti ' + area + '.<br><b>Souřadnice</b> Lat: ' + latitude + \
           ' Lon: ' + longitude + '. ' + '<br><b>Čas detekce:</b> ' + earthquake_time + " <br><b>Vzdálenosti od měst:</b> " + distance_list_string + '. <br>Možná pocítění zemětřesení mohou být následující. ' \
           + intensity_info + '<br><b> Zdroj informace:</b> Evropsko-středozemního seismologické centrum. '

    print('TITLE:')
    print(title)
    print('EXCERPT')
    print(excerpt)
    print('BODY')
    print(body)