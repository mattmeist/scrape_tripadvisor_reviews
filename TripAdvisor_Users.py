import json # A lot of data online is stored as jsons
import pandas as pd
import re # Regular expressions, to help us parse html, json.
import requests # To pull internet pages
import time # To allow us to "sleep" the scraping, so as not to overwhelm the servers
import os # To create folders
import math
from bs4 import BeautifulSoup # To make html easier to parse

# Function to create a directory if it doesn't exist
def create_directory(directory):
    if not os.path.exists(directory):
        os.mkdir(directory)
        print(f"Directory '{directory}' created.")
    else:
        print(f"Directory '{directory}' already exists.")

# Create directories if they don't exist
create_directory(f"Users_Reviews")

def fetch_user_reviews(userId, url, headers):
    rows = []
    userPage = 0
    u_payload = [{
        "variables": {
            "username": f"{userId}",
            "reset": False,
            "allowedTypes": ["REVIEW"],
            "sessionType": "DESKTOP",
            "puid": None,
            "preloadForumPostIds": [],
            "preloadLinkPostIds": [],
            "preloadPhotoIds": [],
            "preloadMediaBatchIds": [],
            "preloadRepostIds": [],
            "preloadReviewIds": [],
            "preloadVideoIds": [],
            "socialReference": True,
            "shouldFetchTripsStatuses": False,
            "requestUid": int(userPage),
            "goBackwards": False
        },
        "extensions": {
            "preRegisteredQueryId": "991491c725fc1626"
        }
    }]

    for attempt in range(10):
        try:
            response = requests.post(url, headers=headers, data=json.dumps(u_payload))
            content = response.json()
            totalReviews = content[0]['data']['memberProfiles'][0]['contributionCounts']['sumReview']
            userPages = list(range(math.ceil(totalReviews/20)))[1:]
            reviews = content[0]['data']['socialFeed']['sections']
            for review in reviews:
                review = review['items'][0]
                row = {
                    'review_id': review['object'].get('id') if review['object'].get('id') else None,
                    'review_language': review['object'].get('language') if review['object'].get('language') else None,
                    'review_status': review['object'].get('reviewStatus') if review['object'].get('reviewStatus') else None,
                }

                if review['object'].get('location'):
                    row.update({
                        'review_locationId': review['object'].get('location').get('locationId') if review['object'].get('location').get('locationId') else None,
                        'review_locationName': review['object'].get('location').get('name') if review['object'].get('location').get('name') else None,
                        'review_placeType': review['object'].get('location').get('placeType') if review['object'].get('location').get('placeType') else None,
                        'review_parentGeoId': review['object'].get('location').get('parentGeoId') if review['object'].get('location').get('parentGeoId') else None,
                    })

                    if review['object'].get('location').get('parent'):
                        row['review_parentLocationId'] = review['object'].get('location').get('parent').get('locationId') if review['object'].get('location').get('parent').get('locationId') else None
                    else:
                        row['review_parentLocationId'] = None
                else:
                    row.update({
                        'review_locationId': None,
                        'review_locationName': None,
                        'review_placeType': None,
                        'review_parentGeoId': None,
                        'review_parentLocationId': None,
                    })

                row.update({
                    'review_title': review['object'].get('title') if review['object'].get('title') else None,
                    'review_helpfulVotes': review['object'].get('helpfulVotes') if review['object'].get('helpfulVotes') else None,
                    'review_createdDate': review['object'].get('createdDate') if review['object'].get('createdDate') else None,
                    'review_publishedDate': review['object'].get('publishedDate') if review['object'].get('publishedDate') else None,
                    'review_rating': review['object'].get('rating') if review['object'].get('rating') else None,
                    'review_text': review['object'].get('text') if review['object'].get('text') else None,
                    'review_photoIds': review['object'].get('photoIds') if review['object'].get('photoIds') else None,
                    'review_userId': review['object'].get('userId') if review['object'].get('userId') else None,
                    'review_tripInfo': review['object'].get('tripInfo') if review['object'].get('tripInfo') else None,
                })
                rows.append(row)

        except:
            if attempt < 10 - 1:  # Retry until the last attempt
                time.sleep(60)
            else:
                raise RuntimeError(f"Failed after multiple attempts: {e}")

    for userPage in userPages:
        u_payload = [{
            "variables": {
                "username": f"{userId}",
                "reset": False,
                "allowedTypes": ["REVIEW"],
                "sessionType": "DESKTOP",
                "puid": None,
                "preloadForumPostIds": [],
                "preloadLinkPostIds": [],
                "preloadPhotoIds": [],
                "preloadMediaBatchIds": [],
                "preloadRepostIds": [],
                "preloadReviewIds": [],
                "preloadVideoIds": [],
                "socialReference": True,
                "shouldFetchTripsStatuses": False,
                "requestUid": int(userPage),
                "goBackwards": False
            },
            "extensions": {
                "preRegisteredQueryId": "991491c725fc1626"
            }
        }]

        response = requests.post(url, headers=headers, data=json.dumps(u_payload))
        for attempt in range(10):
            try:
                content = response.json()

                reviews = content[0]['data']['socialFeed']['sections']
                for review in reviews:
                    review = review['items'][0]
                    row = {
                        'review_id': review['object'].get('id') if review['object'].get('id') else None,
                        'review_language': review['object'].get('language') if review['object'].get('language') else None,
                        'review_status': review['object'].get('reviewStatus') if review['object'].get('reviewStatus') else None,
                    }

                    if review['object'].get('location'):
                        row.update({
                            'review_locationId': review['object'].get('location').get('locationId') if review['object'].get('location').get('locationId') else None,
                            'review_locationName': review['object'].get('location').get('name') if review['object'].get('location').get('name') else None,
                            'review_placeType': review['object'].get('location').get('placeType') if review['object'].get('location').get('placeType') else None,
                            'review_parentGeoId': review['object'].get('location').get('parentGeoId') if review['object'].get('location').get('parentGeoId') else None,
                        })

                        if review['object'].get('location').get('parent'):
                            row['review_parentLocationId'] = review['object'].get('location').get('parent').get('locationId') if review['object'].get('location').get('parent').get('locationId') else None
                        else:
                            row['review_parentLocationId'] = None
                    else:
                        row.update({
                            'review_locationId': None,
                            'review_locationName': None,
                            'review_placeType': None,
                            'review_parentGeoId': None,
                            'review_parentLocationId': None,
                        })

                    row.update({
                        'review_title': review['object'].get('title') if review['object'].get('title') else None,
                        'review_helpfulVotes': review['object'].get('helpfulVotes') if review['object'].get('helpfulVotes') else None,
                        'review_createdDate': review['object'].get('createdDate') if review['object'].get('createdDate') else None,
                        'review_publishedDate': review['object'].get('publishedDate') if review['object'].get('publishedDate') else None,
                        'review_rating': review['object'].get('rating') if review['object'].get('rating') else None,
                        'review_text': review['object'].get('text') if review['object'].get('text') else None,
                        'review_photoIds': review['object'].get('photoIds') if review['object'].get('photoIds') else None,
                        'review_userId': review['object'].get('userId') if review['object'].get('userId') else None,
                        'review_tripInfo': review['object'].get('tripInfo') if review['object'].get('tripInfo') else None,
                    })
                    rows.append(row)

            except (requests.exceptions.RequestException, KeyError, IndexError, TypeError) as e:
                if attempt < 10 - 1:  # Retry until the last attempt
                    time.sleep(60)
                else:
                    raise RuntimeError(f"Failed after multiple attempts: {e}")

    user_reviews = rows
    return user_reviews

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

url = "https://www.tripadvisor.com/data/graphql/ids"

# Read in userId csvs
with open(file, 'r', encoding='utf-8') as file:
        userDF = file.read()
userIds = list(userDF['userId'])

for userId in userIds:
  userReviews = pd.DataFrame(fetch_user_reviews(userId, url, headers)).drop_duplicates()
  userReviews.to_csv(f'User_Reviews/{userId}.csv', index=False)
  time.sleep(2)