# This code will:
# Allow you to specify a city and geoId from tripadvisor.com
# You can find this on their website. 
# geoId: The geoId is the number that follows the "g" in the URL. I would search for
# a single attraction you are interested in, and find their geoId/city name.
# For example, if I wanted to find every attraction in Mitchell, South Dakota:
## I would search for the "Corn Palace", click on the link, and see the URL is:
## https://www.tripadvisor.com/Attraction_Review-g54718-d145077-Reviews-Corn_Palace-Mitchell_South_Dakota.html
## In this case, the geoId is "54718" and the city_name is "Mitchell_South_Dakota"
geoId = "54718" 
city = "Mitchell_South_Dakota"
# Cool.

# Loadin some libraries
import json # A lot of data online is stored as jsons
import pandas as pd
import re # Regular expressions, to help us parse html, json.
import requests # To pull internet pages
import time # To allow us to "sleep" the scraping, so as not to overwhelm the servers
from datetime import datetime, timedelta
import os # To create folders
import math
from bs4 import BeautifulSoup # To make html easier to parse

import selenium
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

# Chrome options
chrome_options = Options()
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--start-maximized")

# Path to ChromeDriver
chrome_driver_path = "chromedriver-mac-arm64/chromedriver" 

service = Service(chrome_driver_path)
chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")

# Function to create a directory if it doesn't exist
def create_directory(directory):
    if not os.path.exists(directory):
        os.mkdir(directory)
        print(f"Directory '{directory}' created.")
    else:
        print(f"Directory '{directory}' already exists.")

# Flatten dictionaries function
def flatten_dict(d, parent_key='', sep='_'):
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

# Create directories if they don't exist
create_directory(f"Attractions_{city}")
create_directory(f"Attractions_{city}_Reviews")
create_directory(f"Attractions_{city}_Questions")
create_directory(f"Attractions_{city}_Answers")

# Function to find links for tokens
def find_links_index(content):
    for idx, item in enumerate(content):
        if 'links' in item:
            return idx
    raise ValueError("No item with a 'links' key was found.")
    
# Function to fetch reviews.
# This is a bit of brute force. This is written so that it will definitely get 
# any page that is available, but may take forever to do so. You can change that
# by turning down (or up??) the `attempts` argument.

    
#Create review fetch function
def fetch_reviews(page, geoId, detailId, attraction, token, url, relative_url):
    rows = []
    offset = int(page * 10)
    
    # Define payload
    payload = [{
        "variables": {
            "pageName": "Attraction_Review",
            "relativeUrl": relative_url,
            "parameters": [
                {"key": "geoId", "value": str(geoId)},
                {"key": "detailId", "value": str(detailId)},
                {"key": "offset", "value": str(offset)}
            ],
            "route": {
                "page": "Attraction_Review",
                "params": {
                    "geoId": geoId,
                    "detailId": detailId,
                    "offset": offset
                }
            },
            "routingLinkBuilding": False
        },
        "extensions": {"preRegisteredQueryId": "211573a2b002568c"}
    },
    {
        "variables": {
            "page": "Attraction_Review",
            "pos": "en-US",
            "parameters": [
                {"key": "geoId", "value": str(geoId)},
                {"key": "detailId", "value": str(detailId)},
                {"key": "offset", "value": str(offset)}
            ],
            "factors": ["TITLE", "META_DESCRIPTION", "MASTHEAD_H1", "MAIN_H1", "IS_INDEXABLE", "RELCANONICAL"],
            "route": {
                "page": "Attraction_Review",
                "params": {
                    "geoId": geoId,
                    "detailId": detailId,
                    "offset": offset
                }
            },
            "currencyCode": "USD"
        },
        "extensions": {"preRegisteredQueryId": "18d4572907af4ea5"}
    },
    {
        "variables": {
            "request": {
                "tracking": {"screenName": "Attraction_Review", "pageviewUid": None},
                "routeParameters": {"contentType": "attraction", "contentId": f"{detailId}"},
                "clientState": None,
                "updateToken": token
            },
            "commerce": {},
            "sessionId": None,
            "tracking": {"screenName": "Attraction_Review", "pageviewUid": None},
            "currency": "USD",
            "currentGeoPoint": None,
            "unitLength": "MILES"
        },
        "extensions": {"preRegisteredQueryId": "a485e0bc56f398b0"}
    }]

    # Define headers
    headers = {
        "Content-Type": "application/json",
        "Accept": "*/*",
        "Sec-Fetch-Site": "same-origin",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Host": "www.tripadvisor.com",
        "Origin": "https://www.tripadvisor.com",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0.1 Safari/605.1.15",
        "Referer": f"https://www.tripadvisor.com{relative_url}",
        "Connection": "keep-alive",
        "Sec-Fetch-Dest": "empty"
    }

    # Retry logic
    for attempt in range(10):
        try:
            response = requests.post(url, headers=headers, data=json.dumps(payload))
            response.raise_for_status()  # Catch HTTP errors
            content = response.json()[2]['data']['Result'][0]['detailSectionGroups'][0]['detailSections'][0]['tabs'][0]['content']
            break
        except (requests.exceptions.RequestException, KeyError, IndexError, TypeError) as e:
            if attempt < 10 - 1:  # Retry until the last attempt
                time.sleep(60)
            else:
                raise RuntimeError(f"Failed after multiple attempts: {e}")

    # Parse reviews
    try:
        for review in content:
            if review.get('userProfile', {}) == {}:
                next
            else:
                owner_response = review.get('ownerResponse', {})
                if owner_response:
                    if owner_response.get('positionAtLocation', {}):
                        owner_response_position = owner_response.get('positionAtLocation', {}).get('text', {})
                    else:
                        owner_response_position = None

                    if owner_response.get('publishedDate', {}):
                        owner_response_date = owner_response.get('publishedDate', {}).get('text', {}) if owner_response.get('publishedDate', {}).get('text', {}) else None
                    else:
                        owner_response_date = None
                else:
                    owner_response_position = None
                    owner_response_date = None

                user_profile = review.get('userProfile', {})
                user_profile_image = user_profile.get('profileImage', {}) if user_profile else None

                if user_profile_image:
                    if user_profile_image.get('photoSizes', [{}]):
                        upi = user_profile_image.get('photoSizes', [{}])[0].get('url')
                    else:
                        upi = None
                else:
                    upi = None

                if review.get('supplierName', {}):
                    if review.get('supplierName', {}).get('text', {}):
                        supplier = review.get('supplierName', {}).get('text', {}).get('text')
                    else:
                        supplier = None
                else:
                    supplier = None

                row = {
                    "review_id": review.get('helpfulVote', {}).get('helpfulVoteAction', {}).get('objectId'),
                    "rating_number": review.get('bubbleRatingNumber'),
                    "rating_text": review.get('bubbleRatingText', {}).get('text') if review.get('bubbleRatingText', {}) else None,
                    "review_title": review.get('htmlTitle', {}).get('text') if review.get('htmlTitle', {}) else None,
                    "review_text": review.get('htmlText', {}).get('text') if review.get('htmlText', {}) else None,
                    "published_date": review.get('publishedDate', {}).get('text') if review.get('publishedDate', {}) else None,
                    "helpful_votes": review.get('helpfulVote', {}).get('helpfulVotes', {}).get('text') if review.get('helpfulVote', {}).get('helpfulVotes', {}) else None,
                    "review_link": review.get('cardLink', {}).get('webRoute', {}).get('webLinkUrl') if review.get('cardLink', {}).get('webRoute', {}) else None,
                    "reviewer_name": user_profile.get('localizedDisplayName', {}).get('text') if user_profile.get('localizedDisplayName', {}) else None,
                    "reviewer_contributions": user_profile.get('contributionCount', {}).get('text') if user_profile.get('contributionCount', {}) else None,
                    "reviewer_url": user_profile.get('profileRoute', {}).get('webLinkUrl') if user_profile.get('profileRoute', {}) else None,
                    "profile_image_url": upi if upi else None,
                    "reviewed_item": supplier if supplier else None,
                    "owner": owner_response.get('displayName') if owner_response else None,
                    "owner_id": owner_response.get('ownerResponseId', {}) if owner_response else None,
                    "owner_response_position": owner_response_position if owner_response_position else None,
                    "owner_response_date": owner_response_date if owner_response_date else None,
                    "owner_response_text": owner_response.get('text', {}) if owner_response else None
                }
                rows.append(row)

    except:
        print(f"Collected, but could not parse page: {page}")
        try:
            for review in content:
                if review.get('userProfile', {}) == {}:
                    next
                else:
                    user_profile = review.get('userProfile', {})

                    if review.get('supplierName', {}):
                        if review.get('supplierName', {}).get('text', {}):
                            supplier = review.get('supplierName', {}).get('text', {}).get('text')
                        else:
                            supplier = None
                    else:
                        supplier = None

                    row = {
                        "review_id": review.get('helpfulVote', {}).get('helpfulVoteAction', {}).get('objectId'),
                        "rating_number": review.get('bubbleRatingNumber'),
                        "rating_text": review.get('bubbleRatingText', {}).get('text') if review.get('bubbleRatingText', {}) else None,
                        "review_title": review.get('htmlTitle', {}).get('text') if review.get('htmlTitle', {}) else None,
                        "review_text": review.get('htmlText', {}).get('text') if review.get('htmlText', {}) else None,
                        "published_date": review.get('publishedDate', {}).get('text') if review.get('publishedDate', {}) else None,
                        "helpful_votes": "NA",
                        "review_link": "NA",
                        "reviewer_name": user_profile.get('localizedDisplayName', {}).get('text') if user_profile.get('localizedDisplayName', {}) else None,
                        "reviewer_contributions": "NA",
                        "reviewer_url": user_profile.get('profileRoute', {}).get('webLinkUrl') if user_profile.get('profileRoute', {}) else None,
                        "profile_image_url": "NA",
                        "reviewed_item": supplier if supplier else None,
                        "owner": "NA",
                        "owner_id": "NA",
                        "owner_response_position": "NA",
                        "owner_response_date": "NA",
                        "owner_response_text": "NA"
                    }
                    rows.append(row)
        except:
            print(f"Collected, but could not (simple) parse page: {page}")

    return rows, content[find_links_index(content)]

def fetch_questions(geoId, detailId, attraction, max_qs, limit, url, headers, relative_url):
    questions_df = []
    # Get batches of Qs at a time
    q_requests = math.ceil(max_qs/limit)

    for q_request in list(range(q_requests)):
        q_offset = q_request * limit
        # Define payload
        q_payload = [{
            "variables": {
                "locationId": detailId,
                "offset": q_offset,
                "limit": limit
            },
            "extensions": {
                "preRegisteredQueryId": "0e34fba657dd66cf"
            }
        }]



        # Define headers
        headers = {
            "Content-Type": "application/json",
            "Accept": "*/*",
            "Sec-Fetch-Site": "same-origin",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Host": "www.tripadvisor.com",
            "Origin": "https://www.tripadvisor.com",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0.1 Safari/605.1.15",
            "Referer": f"https://www.tripadvisor.com{relative_url}",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty"
        }

        # Retry logic
        for attempt in range(10):
            try:
                q_response = requests.post(url, headers=headers, data=json.dumps(q_payload))
                q_response.raise_for_status()  # Catch HTTP errors
                questions = q_response.json()[0]['data']['questions'][0]['questions']
                for question in questions:
                    flat_question = flatten_dict(question)
                    if 'memberProfile_avatar_data_sizes' in flat_question:
                        del flat_question['memberProfile_avatar_data_sizes']

                    if 'topAnswer_memberProfile_avatar_data_sizes' in flat_question:
                        del flat_question['topAnswer_memberProfile_avatar_data_sizes']
                    questions_df.append(flat_question)
                time.sleep(4)
                break
            except (requests.exceptions.RequestException, KeyError, IndexError, TypeError) as e:
                if attempt < 10 - 1:  # Retry until the last attempt
                    time.sleep(30)
                else:
                    raise RuntimeError(f"Failed after multiple attempts: {e}")

    return questions_df

def fetch_answers(geoId, detailId, attraction, questions_df, headers, url, relative_url):
    answers_df = []
    for index, row in questions_df.iterrows():
        if pd.isna(row['topAnswer_id']):
            next
        else:
            time.sleep(2)
            a_payload = [{
                "variables": {
                    "questionId": int(row['id'])
                },
                "extensions": {
                    "preRegisteredQueryId": "3228d8dc53caf10f"
                }
            }]

            for attempt in range(10):
                try:
                    a_response = requests.post(url, headers=headers, data=json.dumps(a_payload))
                    a_response.raise_for_status()  # Catch HTTP errors
                    answers = a_response.json()[0]['data']['QuestionsAndAnswers_getAnswersForQuestions'][0]['answers']
                    for answer in answers:
                            flat_answer = flatten_dict(answer)
                            if 'memberProfile_avatar_data_sizes' in flat_answer:
                                del flat_answer['memberProfile_avatar_data_sizes']
                            answers_df.append(flat_answer)
                    break
                except (requests.exceptions.RequestException, KeyError, IndexError, TypeError) as e:
                    if attempt < 10 - 1:  # Retry until the last attempt
                        time.sleep(30)
                    else:
                        raise RuntimeError(f"Failed after multiple attempts: {e}")
    return answers_df
  
# Collect the top attractions in your city
## Note: This won't get everything. Just what's on the landing page. I may update
## this over time, but for now... no.
driver = webdriver.Chrome(service=service, options=chrome_options)
driver.set_page_load_timeout(300)

city_url = f"https://www.tripadvisor.com/Attractions-g{geoId}-Activities-oa0-{city}.html"
driver.get(city_url)
time.sleep(4)  
page_source = driver.page_source
html = BeautifulSoup(page_source, "html.parser")

# Find attractions
links = html.find_all('div', class_="alPVI eNNhq PgLKC tnGGX")
attractions = []
for link in links:
    href = None
    reviews = None
    
    if link.find('a'):
        href = link.find('a').get('href')
        reviews = link.find('span', class_="biGQs _P pZUbB osNWb").text
        reviews = int(re.sub(r'\D', '', reviews)) if reviews else None
        
        attractions.append({'href': href, 'reviews': reviews})

# Save the extracted results
attractions = pd.DataFrame(attractions)
attractions = attractions.sort_values(by='reviews', ascending=False).reset_index(drop=True)

# Regex pattern to extract geoId, detailId, and attraction name
pattern = r'-g(\d+)-d(\d+)-(.*)\.'
attractions[['geoId', 'detailId', 'attraction']] = attractions['href'].str.extract(pattern)
attractions.to_csv(f'Attractions_{city}.csv', index=False)

# Now, actually do the thing!
# URL for all API calls
url = "https://www.tripadvisor.com/data/graphql/ids"

for index, row in attractions.iterrows():
    # Access each column
    geoId = row['geoId']
    detailId = row['detailId']
    attraction = re.search("Reviews-(\w+)-", row['attraction'])[1]
    start_url = f"https://www.tripadvisor.com{row['href']}"
    print(start_url)
    
    # Get URL
    driver.get(start_url)
    time.sleep(4)  
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, "html.parser")
    pages = list(range(math.ceil(int(re.search(r'of\s([\d,]+)', soup.find('section', id='REVIEWS').find('div', class_='Ci').text).group(1).replace(',', ''))/10)))
    relative_url = f"/Attraction_Review-g{geoId}-d{detailId}-Reviews-{attraction}-{city}.html"
    max_qs = int(re.search("([\d,]+)\sq",soup.find('section', id='REVIEWS').find("div", id="tab-qa-content").find('span', class_="biGQs _P XWJSj Wb").text)[1])
    runtime = math.ceil((len(pages)*3.6 + 
                         math.ceil(max_qs/50*2) + 
                         math.ceil(max_qs*2))/60/6)/10
    reviews_runtime = math.ceil((len(pages)*3.6)/60/6)/10
    questions_runtime = round((max_qs/50*2.6)/60/60,5)
    answers_runtime = math.ceil((math.ceil(max_qs*2.6))/60)/60
    starttime = datetime.now().strftime('%I:%M %p')
    finishtime = (datetime.now() + timedelta(hours=runtime)).strftime('%I:%M %p')
    print(f"Scraping {attraction}: \n Starting at {starttime}. Will take ~{runtime} hours.")
    print(f"\tReviews: {reviews_runtime} hours; {(datetime.now() + timedelta(hours=reviews_runtime)).strftime('%I:%M %p')}.")
    print(f"\tQuestions: {math.ceil(questions_runtime*3600)} seconds.")
    print(f"\tAnswers: {math.ceil(answers_runtime*60)} minutes; {(datetime.now() + timedelta(hours=questions_runtime+reviews_runtime+answers_runtime)).strftime('%I:%M %p')}.")

    all_reviews = []
    start_url = f"/Attraction_Review-g{geoId}-d{detailId}-Reviews-{attraction}-{city}.html"
    for page in pages:
        if page == 0:
            #Get next page
            token = re.search("updateToken%5C%5C%5C%22%3A%5C%5C%5C%22(.*?)%5C%5C%5C%22", page_source)[1]
            relative_url = f"/Attraction_Review-g{geoId}-d{detailId}-Reviews-or{(page+1)*10}-{attraction}-{city}.html"

        else:
            offset = int(page*10)
            relative_url = f"/Attraction_Review-g{geoId}-d{detailId}-Reviews-or{offset}-{attraction}-{city}.html"

            #Get reviews
            for attempt in range(10):
                try:
                    reviews, links = fetch_reviews(page, geoId, detailId, attraction, token, url, relative_url)
                    all_reviews.extend(reviews)  # Extend adds all rows (a list of dictionaries) to the list
                    break
                except (requests.exceptions.RequestException, KeyError, IndexError) as e:
                    if attempt < 10 - 1:  # Retry until the last attempt
                        time.sleep(10)
                    else:
                        raise RuntimeError(f"Failed after multiple attempts: {e}")

            # Collect back token when this is second page, collect prior page
            if page == 1:
                back_token = links['links'][0]['updateLink']['updateToken']
                reviews = fetch_reviews(page, geoId, detailId, attraction, back_token, url, re.search("(/Attraction.*$)",start_url)[1])[0]
                all_reviews.extend(reviews)  # Extend adds all rows (a list of dictionaries) to the list
            # Update tokens
            if len(links['links']) == 3:
                token = links['links'][1]['updateLink']['updateToken']
            else:
                token = links['links'][2]['updateLink']['updateToken']

        time.sleep(3)

        if page % 50 == 0:
            df = pd.DataFrame(all_reviews).drop_duplicates()
            df.to_csv(f'Attractions_{city}_Reviews/{attraction}.csv', index=False)

    df = pd.DataFrame(all_reviews).drop_duplicates()
    df.to_csv(f'Attractions_{city}_Reviews/{attraction}.csv', index=False)
    print(f"\n Reviews finished at {datetime.now().strftime('%I:%M %p')}. \n\tN = {len(df):,}.")
    
    limit = 50
    relative_url = f"/Attraction_Review-g{geoId}-d{detailId}-Reviews-{attraction}-{city}.html"
    # Define headers
    headers = {
        "Content-Type": "application/json",
        "Accept": "*/*",
        "Sec-Fetch-Site": "same-origin",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Host": "www.tripadvisor.com",
        "Origin": "https://www.tripadvisor.com",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0.1 Safari/605.1.15",
        "Referer": f"https://www.tripadvisor.com{relative_url}",
        "Connection": "keep-alive",
        "Sec-Fetch-Dest": "empty"
    }
    if i < 2:
        questions_df = pd.DataFrame(fetch_questions(geoId, detailId, attraction, max_qs, limit, url, headers, relative_url)).drop_duplicates()
        questions_df.to_csv(f'Attractions_{city}_Questions/{attraction}.csv', index=False)
        print(f" Questions finished at {datetime.now().strftime('%I:%M %p')}. \n\tN = {len(questions_df):,}.")
        answers_df = pd.DataFrame(fetch_answers(geoId, detailId, attraction, questions_df, headers, url, relative_url)).drop_duplicates()
        answers_df.to_csv(f'Attractions_{city}_Answers/{attraction}.csv', index=False) 
        print(f" Answers finished at {datetime.now().strftime('%I:%M %p')}. \n\tN = {len(answers_df):,}.")
        i += 1
    elif i > 3:
        questions_df = pd.DataFrame(fetch_questions(geoId, detailId, attraction, max_qs, limit, url, headers, relative_url)).drop_duplicates()
        questions_df.to_csv(f'Attractions_{city}_Questions/{attraction}.csv', index=False)
        print(f" Questions finished at {datetime.now().strftime('%I:%M %p')}. \n\tN = {len(questions_df):,}.")
        answers_df = pd.DataFrame(fetch_answers(geoId, detailId, attraction, questions_df, headers, url, relative_url)).drop_duplicates()
        answers_df.to_csv(f'Attractions_{city}_Answers/{attraction}.csv', index=False) 
        print(f" Answers finished at {datetime.now().strftime('%I:%M %p')}. \n\tN = {len(answers_df):,}.")
        i += 1
    else:
        i += 1
        next
               
