import sys
import traceback
import urllib
from xml.etree import ElementTree
import urllib3
import xmltodict
from bs4 import BeautifulSoup
from capparselib.parsers import CAPParser
import schedule
import onesignal as onesignal_sdk
import mysql.connector
from slugify import slugify
import time
from mailchimp3 import MailChimp
import tweepy
import re
import ssl
from string import Template
import facebook
import os
import mail_sender
import urllib.request
import xml.etree.ElementTree as ET
from geopy.geocoders import Nominatim
from timezoneconverter import convert
from dateutil import parser

is_production = os.environ.get('IS_HEROKU', None)

DB_USER = os.environ.get('DB_USER')
DB_PASSWORD = os.environ.get('DB_PASSWORD')
DB_NAME = os.environ.get('DB_NAME')

ONESIGNAL_USER_AUTH_KEY = os.environ.get('ONESIGNAL_USER_AUTH_KEY')
ONESIGNAL_APP_AUTH_KEY = os.environ.get('ONESIGNAL_APP_AUTH_KEY')
ONESIGNAL_APP_ID = os.environ.get('ONESIGNAL_APP_ID')

TWITTER_CONSUMER_KEY = os.environ.get('TWITTER_CONSUMER_KEY')
TWITTER_CONSUMER_SECRET = os.environ.get('TWITTER_CONSUMER_SECRET')
TWITTER_ACCESS_TOKEN = os.environ.get('TWITTER_ACCESS_TOKEN')
TWITTER_ACCESS_TOKEN_SECRET = os.environ.get('TWITTER_ACCESS_TOKEN_SECRET')

FACEBOOK_PAGE_ACCESS_TOKEN = os.environ.get('FACEBOOK_PAGE_ACCESS_TOKEN')

MAILCHIMP_API_KEY = os.environ.get('MAILCHIMP_API_KEY')
MAILCHIMP_USER_NAME = os.environ.get('MAILCHIMP_USER_NAME')


def getxml():
    url = "http://portal.chmi.cz/files/portal/docs/meteo/om/bulletiny/XOCZ50_OKPR.xml"

    resource = urllib.request.urlopen(url)

    try:
        data = resource.read().decode(resource.headers.get_content_charset())
    except:
        print("Failed to parse xml from response (%s)" % traceback.format_exc())
    return data


def getcategory(cap_event):
    if 'teplot' in cap_event.lower():
        return 142, 'heat.webp'
    elif 'vítr' in cap_event.lower():
        return 152, 'windstorm.jpg'
    elif 'sněžení' in cap_event.lower() or 'sníh' in cap_event.lower() or 'sněhové' in cap_event.lower() or 'sněh' in cap_event.lower():
        return 162, 'snowstorm.jpg'
    elif 'náledí' in cap_event.lower():
        return 172, 'black-ice.jpg'
    elif 'ledovka' in cap_event.lower() or 'námraza' in cap_event.lower() or 'mráz' in cap_event.lower():
        return 182, 'black-ice.jpg'
    elif 'bouřk' in cap_event.lower():
        return 3, 'thunderstorm.jpg'
    elif 'déšť' in cap_event.lower():
        return 202, 'rainfall.jpg'
    elif 'povodně' in cap_event.lower() or 'povod' in cap_event.lower() or 'povodeň' in cap_event.lower():
        return 212, 'flooding.jpg'
    elif 'požár' in cap_event.lower() or 'žár' in cap_event.lower():
        return 222, 'fire.jpg'
    elif 'ozón' in cap_event.lower():
        return 232, 'ozone.jpg'
    elif 'prach' in cap_event.lower():
        return 242, 'dust.png'
    elif 'oxid' in cap_event.lower() and 'dusičitý' in cap_event.lower():
        return 252, 'nitrogen-dioxide.jpg'
    elif 'oxid' in cap_event.lower() and 'siřičitý' in cap_event.lower():
        return 262, 'sulfur-dioxide.jpg'
    elif 'jiný' in cap_event.lower() or 'jiné' in cap_event.lower():
        return 272, 'other.jpg'
    else:
        return 7, 'other.jpg'


def send_one_signal(notification_title):
    onesignal_client = onesignal_sdk.Client(user_auth_key=ONESIGNAL_USER_AUTH_KEY,
                                            app_auth_key=ONESIGNAL_APP_AUTH_KEY,
                                            app_id=ONESIGNAL_APP_ID)

    # create a notification
    new_notification = onesignal_sdk.Notification(post_body={
        "contents": {"en": notification_title, "tr": notification_title},
        "included_segments": ["Subscribed Users"]
    })

    # send notification, it will return a response
    onesignal_response = onesignal_client.send_notification(new_notification)
    print(onesignal_response.status_code)
    print(onesignal_response.json())


def send_tweet(title_text, slug, type, topic):

    consumer_key = TWITTER_CONSUMER_KEY
    consumer_secret = TWITTER_CONSUMER_SECRET
    access_token = TWITTER_ACCESS_TOKEN
    access_token_secret = TWITTER_ACCESS_TOKEN_SECRET

    hashtags = ""

    if(topic == "coronavirus"):
        hashtags = "#koronavir #COVID19 #pandemie"
    elif(topic == "hydrometeo"):
        hashtags = "@CHMUCHMI #česko #czechia"
    elif(topic == "earthquake"):
        hashtags = "@LastQuake #zemětřesení"

    tweet_text = "NOVÉ " + type + " | " + title_text + " Více podrobností na " + "https://varovny-system.herokuapp.com/varovani/" + slug + hashtags

    # authentication of consumer key and secret
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)

    # authentication of access token and secret
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth)

    # update the status
    api.update_status(tweet_text)


def send_mailchimp(title_text, excerpt_text, body_text, slug):

    client = MailChimp(mc_api=MAILCHIMP_API_KEY, mc_user=MAILCHIMP_USER_NAME)

    campaign_name = title_text
    audience_id = "c52f3d1bc0"
    from_name = "Varovný systém ČR"
    reply_to = "disaster-warning-system@outlook.com"

    data = {
        "recipients":
            {
                "list_id": audience_id
            },
        "settings":
            {
                "subject_line": campaign_name,
                "from_name": from_name,
                "reply_to": reply_to
            },
        "type": "regular"
    }

    new_campaign = client.campaigns.create(data=data)
    campaign_id = new_campaign['id']

    html_code = '<h1>Varovný systém ČR: </h1><h2>' + title_text + '</h2><p><b>' + excerpt_text + '</b></p>' + '<p>' + body_text + '</p> Více podrobností na: ' +  "https://varovny-system.herokuapp.com/warnings/" + slug

    # string_template = Template(html_code).safe_substitute()

    try:
        client.campaigns.content.update(
            campaign_id=campaign_id,
            data={'message': 'Campaign message', 'html': html_code}
        )
    except Exception as error:
        print('Mailchimp Content Edit Error')
        print(error)

    try:
        client.campaigns.actions.send(campaign_id=campaign_id)
    except Exception as error:
        print('Mailchimp Send Error')
        print(error)


def send_facebook(title_text, slug, type, topic):

        hashtags = ""

        if (topic == "coronavirus"):
            hashtags = " #koronavir #COVID19 #pandemie"

        page_access_token = FACEBOOK_PAGE_ACCESS_TOKEN
        graph = facebook.GraphAPI(access_token=page_access_token)

        facebook_post_text = "NOVÉ " + type + " | " + title_text + ". Více podrobností na " + "https://varovny-system.herokuapp.com/varovani/" + slug + hashtags

        graph.put_object(parent_object='me', connection_name='feed', message=facebook_post_text)


def run_emsc_parser(cnx, cursor):
    namespace = {"geo": "http://www.w3.org/2003/01/geo/",
                 "emsc": "https://www.emsc-csem.org"}

    url = 'https://www.emsc-csem.org/service/rss/rss.php?filter=yes&start_date=2020-04-01&min_mag=2.5&region=CZECH+REPUBLIC&min_intens=0&max_intens=8&distance=true'

    ssl._create_default_https_context = ssl._create_unverified_context
    ctx = ssl._create_unverified_context()

    # filter with > 2.5 earthquake magnitudo
    emsc_czech = urllib.request.urlopen(url, context=ctx)

    tree = ET.parse(emsc_czech)

    for item in tree.findall('.//channel/item'):
        message_string = ''

        latitude = item.findall("geo:lat", namespace)[0].text
        longitude = item.findall('geo:long',namespace)[0].text
        magnitude = item.findall('emsc:magnitude',namespace)[0].text

        magnitude_int = float(list(filter(str.isdigit, magnitude))[0])

        distance_list = ''

        for distance in item.findall('distance'):
            distance_list = distance.findall('city')[0].text + distance.findall('city')[1].text + \
                            distance.findall('city')[2].text
            distance_list_string = ''.join(str(distance_list_item) for distance_list_item in distance_list)

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
        location = geolocator.reverse(location_string, language='cs',timeout=10)
        address = location.raw['address']
        if address.get('city') is not None:
            area = address.get('city') + ", " + address.get('suburb')
            message_string += ", " + area
            title += ", " + area
        else:
            area = address.get('suburb')
            message_string += ", " + area
            title += ", " + area

        earthquake_time_utc = item.findall('emsc:time',namespace)[0].text
        link_emsc = item.findall('link')[0].text

        earthquake_time = convert(earthquake_time_utc)

        message_string += ", " + earthquake_time
        title += ", " + earthquake_time

        excerpt = intensity_info + ' Další podrobnosti o zemětřesení najdete na' \
                                   ' <a href=\"' + link_emsc + '\">webu Evropsko-středozemního seismologického centra</a>' \
                                                               '<iframe style="height: 300px" width="600" height="300" frameborder="0" style="border:0" ' \
                                                               'src="https://www.google.com/maps/embed/v1/place?q=' + latitude + '%20' + longitude + '&key=AIzaSyBpDMxrsrKQKYMXYDNbzsIEq5mfddz-bVk&zoom=11" allowfullscreen></iframe>'

        body = 'Zemětřesení bylo detekováno v oblasti ' + area + '.<br><b>Souřadnice</b> Lat: ' + latitude + \
                  ' Lon: ' + longitude + '. ' + '<br><b>Čas detekce:</b> ' + earthquake_time + " <br><b>Vzdálenosti od měst:</b> " + distance_list_string + '. <br>Možná pocítění zemětřesení mohou být následující. ' \
               + intensity_info + '<br><b> Zdroj informace:</b> Evropsko-středozemního seismologické centrum. '

        category_id = 282

        print('Title')
        print(title)
        print('Excerpt:')
        print(excerpt)
        print('Body')
        print(body)

        query = ("SELECT COUNT(1) FROM posts WHERE title = '%s'" % (title))

        cursor.execute(query)

        if cursor.fetchone()[0]:
            print("Record exists.")
        else:
            print("Record doesn't exists.")
            slug = slugify(title)
            try:
                now = time.strftime('%Y-%m-%d %H:%M:%S')
                cursor.execute(
                    """INSERT INTO posts (author_id, title, slug, excerpt, body, image, category_id, created_at, updated_at, published_at) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (22, title, slug, excerpt, body, 'earthquake.jpg', category_id, now, now,
                     now))
                cnx.commit()

                print("INSERTED")

                send_one_signal(message_string)
                print("ONESIGNAL NOTIFICATION SENT")

                send_mailchimp(message_string, excerpt, body, slug)
                print("MAILCHIMP E-MAIL CAMPAIGN SENT")

                send_tweet(message_string, slug, alert_type, "earthquake")
                print("TWEET SENT")

                send_facebook(message_string, slug, alert_type, "earthquake")
                print("FACEBOOK POST SENT")

            except mysql.connector.Error as e:
                print("NOT INSERTED")
                print("Error code:", e.errno)  # error number
                print("SQLSTATE value:", e.sqlstate)  # SQLSTATE value
                print("Error message:", e.msg)  # error message
                print("Error:", e)  # errno, sqlstate, msg values
                s = str(e)
                print("Error:", s)  # errno, sqlstate, msg values
                cnx.rollback()


def run_hygpraha_parser(cnx, cursor):

    url = 'http://www.hygpraha.cz/obsah/koronavirus_506_1.html'

    hygpraha = urllib.request.urlopen(url)

    page_soup = BeautifulSoup(hygpraha, 'html.parser')

    divs_vypis_items = page_soup.find_all('div', {'class': 'vypis-item'})

    for divs_vypis_item in divs_vypis_items:
        h3_vypis_items = divs_vypis_item.findAll('h3')
        p_vypis_item = divs_vypis_item.findAll('p')

        for h3_vypis_item in h3_vypis_items:
            a_vypis_item = h3_vypis_item.findAll('a')
            a_vypis_item_href = h3_vypis_item.find('a')['href']

            if a_vypis_item:
                print('Title:')
                title = 'Hygienická stanice hlavního města Prahy: ' + a_vypis_item[0].text
                title = title[:191]
                print(title)
                excerpt = 'Vydáno na <a href="http://www.hygpraha.cz/" target="_blank">Hygienická stanice Praha</a>'
                if p_vypis_item:
                    href = 'http://www.hygpraha.cz/varovani/' + a_vypis_item_href
                    print('Excerpt:')
                    excerpt = excerpt + ': ' + p_vypis_item[1].text + '. <a href="' + href + '" target="_blank">Klikněte pro více informací.</a>'
                    print(excerpt)
                    print('Body:')
                    body = 'Vydala [Hygienická stanice hlavního města Prahy](http://www.hygpraha.cz//)'
                    body = body + ': ' + p_vypis_item[1].text + ' [Kliněte pro více informací.](' + href + ')</a>'
                    print(body)
                    category_id = 132

                query = ("SELECT COUNT(1) FROM posts WHERE title = '%s'" % (title))

                cursor.execute(query)

                excluded_numbers_of_infected_prague = "pozitivních případů onemocnění"

                if cursor.fetchone()[0]:
                    print("Record exists.")
                elif excluded_numbers_of_infected_prague in title:
                    print("Excluded post.")
                else:
                    print("Record doesn't exists.")
                    slug = slugify(title)
                    try:
                        now = time.strftime('%Y-%m-%d %H:%M:%S')
                        cursor.execute(
                            """INSERT INTO posts (author_id, title, slug, excerpt, body, image, category_id, created_at, updated_at, published_at) 
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                            (22, title, slug, excerpt, body, 'epidemic.jpg', category_id, now, now,
                             now))
                        cnx.commit()
                        print(title)
                        print("INSERTED")

                        send_one_signal(title)
                        print("ONESIGNAL NOTIFICATION SENT")

                        send_mailchimp(title, excerpt, body, slug)
                        print("MAILCHIMP E-MAIL CAMPAIGN SENT")

                        alert_type = "INFO"

                        send_tweet(title, slug, alert_type, "coronavirus")
                        print("TWEET SENT")

                        send_facebook(title, slug, alert_type, "coronavirus")
                        print("FACEBOOK POST SENT")

                    except mysql.connector.Error as e:
                        print("NOT INSERTED")
                        print("Error code:", e.errno)  # error number
                        print("SQLSTATE value:", e.sqlstate)  # SQLSTATE value
                        print("Error message:", e.msg)  # error message
                        print("Error:", e)  # errno, sqlstate, msg values
                        s = str(e)
                        print("Error:", s)  # errno, sqlstate, msg values
                        cnx.rollback()


def run_koronavirus_mzcr_parser(cnx, cursor):

    ssl._create_default_https_context = ssl._create_unverified_context
    ctx = ssl._create_unverified_context()

    url = 'https://koronavirus.mzcr.cz/category/mimoradna-opatreni/'

    mzcr = urllib.request.urlopen(url, context=ctx)

    page_soup = BeautifulSoup(mzcr, 'html.parser')

    articles = page_soup.find_all('article')

    for article in articles:
        p_summary = article.find_all('p', {'class': 'summary'})
        ases = article.findAll('a')

        for a in ases:

            h2 = a.find_all('h2')

            if h2:
                print('H2:')
                title = 'Ministerstvo zdravotnictví: ' + h2[0].text
                title = title[:191]
                print('TITLE')
                print(title)
                a_href = a['href']
                href = a_href

                p = re.sub(r'\n\s*\n', r'\n\n', p_summary[0].text.strip(), flags=re.M)
                print('Excerpt:')
                excerpt = 'Vydalo <a href="https://koronavirus.mzcr.cz/">Ministerstvo zdravotnictví ČR</a>'
                excerpt = excerpt + ': ' + p + '. <a href="' + href + '">Klikněte pro více informací.</a>'
                print(excerpt)

                print('Body:')
                body = 'Vydalo [Ministerstvo zdravotnictví ČR](https://koronavirus.mzcr.cz/)'
                body = body + ': ' + p + ' [Kliněte pro více informací.](' + href + ')</a>'
                print(body)
                category_id = 132

                query = ("SELECT COUNT(1) FROM posts WHERE title = '%s'" % (title))

                cursor.execute(query)

                if cursor.fetchone()[0]:
                    print("Record exists.")
                else:
                    print("Record doesn't exists.")
                    slug = slugify(title)
                    try:
                        now = time.strftime('%Y-%m-%d %H:%M:%S')
                        cursor.execute(
                            """INSERT INTO posts (author_id, title, slug, excerpt, body, image, category_id, created_at, updated_at, published_at) 
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                            (22, title, slug, excerpt, body, 'epidemic.jpg', category_id, now, now,
                             now))
                        cnx.commit()
                        print(title)
                        print("INSERTED")

                        send_one_signal(title)
                        print("ONESIGNAL NOTIFICATION SENT")

                        send_mailchimp(title, excerpt, body, slug)
                        print("MAILCHIMP E-MAIL CAMPAIGN SENT")

                        alert_type = "INFO"

                        send_tweet(title, slug, alert_type, "coronavirus")
                        print("TWEET SENT")

                        send_facebook(title, slug, alert_type, "coronavirus")
                        print("FACEBOOK POST SENT")

                    except mysql.connector.Error as e:
                        print("NOT INSERTED")
                        print("Error code:", e.errno)  # error number
                        print("SQLSTATE value:", e.sqlstate)  # SQLSTATE value
                        print("Error message:", e.msg)  # error message
                        print("Error:", e)  # errno, sqlstate, msg values
                        s = str(e)
                        print("Error:", s)  # errno, sqlstate, msg values
                        cnx.rollback()


def run_chmi_parser(cnx,cursor,alert_list):

    for alert in alert_list:
        for alert_info in alert['cap_info']:
            if alert_info['cap_certainty'] != 'Unlikely':
                if alert_info['cap_language'] == 'cs':
                    area = ''
                    for alert_area in alert_info['cap_area']:
                        area += alert_area['area_description'] + ', '
                    print('Title:')
                    title = 'ČHMÚ: ' + alert_info['cap_event'] + ': ' + area
                    if len(title) > 191:
                        title = title[:188]
                        title = title + '...'
                    else:
                        title = title[:191]
                    print(title)
                    print('Excerpt:')

                    try:
                        alert_info['cap_effective']
                    except KeyError:
                        onset_date_time = 'neurčito'
                    else:
                        onset_date_time = alert_info['cap_effective']
                        onset_date_time = onset_date_time + ''
                        onset_date_time = parser.parse(onset_date_time).strftime('%d.%m.%Y %H:%M')
                    try:
                        alert_info['cap_expires']
                    except KeyError:
                        expires_date_time = 'neurčito'
                    else:
                        expires_date_time = alert_info['cap_expires']
                        expires_date_time = expires_date_time + ''
                        expires_date_time = parser.parse(expires_date_time).strftime('%d.%m.%Y %H:%M')

                    # print(alert_info.keys())
                    excerpt = area + ' | ' + alert_info[
                        'cap_description'] + ' | Platnost od: ' + onset_date_time + ' do ' + expires_date_time + ' | <a href="http://portal.chmi.cz/">Vydal Český hydrometeorologický ústav</a>'
                    print(excerpt)
                    print('Body:')
                    body = str(alert_info['cap_instruction'])
                    print(alert_info['cap_instruction'])

                    category_id_recognized, post_image = getcategory(str(alert_info['cap_event']))

                    query = ("SELECT COUNT(1) FROM posts WHERE title = '%s'" % (title))

                    cursor.execute(query)

                    if cursor.fetchone()[0]:
                        print("Record exists.")
                    else:
                        print("Record doesn't exists.")
                        slug = slugify(title)
                        try:
                            now = time.strftime('%Y-%m-%d %H:%M:%S')
                            cursor.execute(
                                """INSERT INTO posts (author_id, title, slug, excerpt, body, image, category_id, created_at, updated_at, published_at) 
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                                (22, title, slug, excerpt, body, post_image,
                                 category_id_recognized, now, now, now))
                            cnx.commit()
                            print(title)
                            print("INSERTED")

                            send_one_signal(title)
                            print("ONESIGNAL NOTIFICATION SENT")

                            send_mailchimp(title, excerpt, body, slug)
                            print("MAILCHIMP E-MAIL CAMPAIGN SENT")

                            alert_type = "VAROVÁNÍ"

                            send_tweet(title, slug, alert_type, "hydrometeo")
                            print("TWEET SENT")

                            send_facebook(title, slug, alert_type, "hydrometeo")
                            print("FACEBOOK POST SENT")

                        except mysql.connector.Error as e:
                            print("NOT INSERTED")
                            print("Error code:", e.errno)  # error number
                            print("SQLSTATE value:", e.sqlstate)  # SQLSTATE value
                            print("Error message:", e.msg)  # error message
                            print("Error:", e)  # errno, sqlstate, msg values
                            s = str(e)
                            print("Error:", s)  # errno, sqlstate, msg values
                            cnx.rollback()


def job():

    try:
        cnx = mysql.connector.connect(user=DB_USER, password=DB_PASSWORD,
                                      host='us-cdbr-iron-east-04.cleardb.net',
                                      database=DB_NAME)

        cursor = cnx.cursor()

        alert_list = CAPParser(getxml()).as_dict()

        # HERE CALL OF PARSERS:

        run_chmi_parser(cnx,cursor,alert_list)
        run_hygpraha_parser(cnx,cursor)
        run_koronavirus_mzcr_parser(cnx,cursor)
        run_emsc_parser(cnx,cursor)

        cursor.close()
        cnx.close()

    except Exception as e:
        trace_back = traceback.format_exc()
        exception_message = str(e) + ", " + trace_back
        mail_sender.send_error_email(exception_message)


schedule.every(30).seconds.do(job)

while 1:
    schedule.run_pending()
    time.sleep(1)
