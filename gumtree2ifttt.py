import os
import requests
import json
from bs4 import BeautifulSoup

scrapings_dir = ''
pageURLs = ['https://www.gumtree.com.au/s-grange-brisbane/l3005788r10',
            'https://www.gumtree.com.au/s-digital-slr/grange-brisbane/c21107l3005788r10'] # URLs to scrape
iftttURL = 'https://maker.ifttt.com/trigger/Gumtree/with/key/{key}' # Your key
# You will NOT recieve notifications for the following categories
filter_categories = ['/fish/',
                     '/desks/',
                     '/car-seats/',
                     '/bookcases-shelves/',
                     '/fridges-freezers/',
                     '/bedside-tables/',
                     '/birds/',
                     '/beds/',
                     '/washing-machines-dryers/',
                     '/sofas/',
                     '/home-phones/',
                     '/entertainment-tv-units/',
                     '/dishwashers/',
                     '/armchairs/',
                     '/ovens/',
                     '/cats-kittens/',
                     '/outdoor-dining-furniture/',
                     '/tool-storage-benches/',
                     '/feeding/',
                     '/cots-bedding/',
                     '/ceiling-lights/',
                     '/pots-garden-beds/',
                     '/dining-tables/',
                     '/coffee-tables/',
                     '/livestock/',
                     '/cabinets/',
                     '/dogs-puppies/']

def scrape_page(page):
    savePath = os.path.join(scrapings_dir, 'gumtree.html')
    results = requests.get(page)
    results_file = open(savePath, 'w')
    with results_file:
        results_file.write(results.text.encode('utf-8', errors='ignore'))
    return savePath
    
def html_parser(filename):
    gumtree_file = open(filename)
    gumtree_contents = gumtree_file.read()
    gtsoup = BeautifulSoup(gumtree_contents, 'lxml')
    master_list = []
    gt_li = gtsoup.findAll('a', attrs = {'class': 'user-ad-row'})
    for node in gt_li:
        if len(node.contents) > 0:
            post_dict = {}
            post_dict['distance'] = node.find('div', attrs = {'class': 'user-ad-row__location'}).contents[2].get_text()
            if len(post_dict['distance']) == 1: continue
            post_dict['link'] = node.get('href')
            if any (category in post_dict['link'] for category in filter_categories): continue
            post_dict['title'] = node.findAll('p', attrs = {'class': 'user-ad-row__title'})[0].string
            post_dict['description'] = node.findAll('p', attrs = {'class': 'user-ad-row__description'})[0].contents[0]
            #~ post_dict['area'] = node.find('span', attrs = {'class': 'user-ad-row__location-area'}).contents[0]
            post_dict['suburb'] = node.find('div', attrs = {'class': 'user-ad-row__location'}).contents[1]
            post_dict['price'] = node.find('div', attrs = {'class': 'user-ad-price'}).get_text()
            #~ if 'Free' in post_dict['price']: post_dict['price'] = ''
            post_dict['ad_id'] = node.get('id')
            master_list.append(post_dict)
    gumtree_file.close()
    os.remove(filename)
    return master_list
    
def new_alert(entry):
    report = {}
    if entry['price'] == '':
        if len(entry['title']) > 50:
            report['value1'] = entry['title'] + '\n' + entry['description'] + '\n' + entry['suburb'] + entry['distance'] + '\n'
        else:
            report['value1'] = entry['description'] + '\n' + entry['suburb'] + entry['distance'] + '\n'
    else:
        if len(entry['title']) > 40:
            report['value1'] = entry['title'] + '. ' + entry['price'] + '\n' + entry['description'] + '\n' + entry['suburb'] + entry['distance'] + '\n'
        else:
            report['value1'] = entry['description'] + '\n' + entry['suburb'] + entry['distance'] + '\n'
        report['value1'] = entry['title'] + '. ' + entry['price'] + '\n' + entry['description'] + '\n' + entry['suburb'] + entry['distance'] + '\n'
    report['value2'] = 'http://gumtree.com.au' + entry['link']
    report['value3'] = entry['title'] + '\n' + entry['price']
    requests.post(iftttURL, data=report)
    
def gumtree_scraper():
    json_file = open('master_file.text','r')
    json_file_contents = json_file.read()
    if not os.stat('master_file.text')[6] == 0:
        old_data = json.loads(json_file_contents)
    else:
        old_data = []
    this_scrape = []
    for page in pageURLs:
        this_scrape.append(html_parser(scrape_page(page)))
        data_ids = []
        new_entries = []
        new_entry_count = 0
        for entry in old_data:
            data_ids.append(entry[u'ad_id'])
        for entry in this_scrape[pageURLs.index(page)]:
            if entry[u'ad_id'] not in data_ids:
                old_data.append(entry)
                new_entry_count += 1
                new_entries.append(entry)
                new_alert(entry)
    json_file.close()
    json_file = open('master_file.text', 'w')
    json_file.write(json.dumps(old_data))
    json_file.close()

gumtree_scraper()
