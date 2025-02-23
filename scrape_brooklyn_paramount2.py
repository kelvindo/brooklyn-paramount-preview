import requests
import json

graphql_endpoint = "https://api.livenation.com/graphql"

query = """
query EVENTS_PAGE($offset: Int!, $venue_id: String!, $include_genres: String, $start_date_time: String, $end_date_time: String) {
  getEvents(
    filter: {exclude_status_codes: ["cancelled", "postponed"], image_identifier: "RETINA_PORTRAIT_16_9", venue_id: $venue_id, start_date_time: $start_date_time, end_date_time: $end_date_time, include_genres: $include_genres}
    limit: 36
    offset: $offset
    order: "ascending"
    sort_by: "start_date"
  ) {
    artists {
      discovery_id
      name
      slug
      images {
        fallback
        image_url
      }
      genre_id
      genre
    }
    discovery_id
    event_date
    event_date_timestamp_utc
    event_end_date
    event_end_time
    event_status_code
    event_time
    event_timezone
    images {
      fallback
      image_url
    }
    important_info
    name
    upsell {
      classification_id
      discovery_id
      name
      type
      url
    }
    url
    venue {
      name
      discovery_id
      location {
        address
        city
        country
        latitude
        longitude
        state
        zip_code
      }
    }
  }
}
"""

headers = {
    "Content-Type": "application/json; charset=UTF-8",  # Include charset
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
    "x-api-key": "da2-jmvb5y2gjfcrrep3wzeumqwgaq",  # The API key!
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
    "Host": "api.livenation.com",
    "Origin": "https://www.brooklynparamount.com",
    "Referer": "https://www.brooklynparamount.com/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "cross-site",
    "sec-ch-ua": '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
    "x-amz-user-agent": "aws-amplify/6.0.21 api/1 framework/2"
}


all_shows = []
offset = 0
venue_id = "KovZpZA77ldA"

while True:
    variables = {
        "offset": offset,
        "venue_id": venue_id,
        # Add start_date_time, end_date_time, include_genres if needed
    }

    payload = {
        "query": query,
        "variables": variables
    }

    try:
        response = requests.post(graphql_endpoint, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

        # print(json.dumps(data, indent=2))  # Uncomment for debugging

        if "errors" in data:
            print(f"GraphQL Errors: {data['errors']}")
            break

        events = data["data"]["getEvents"]
        if not events:
            break

        for event in events:
            try:
                title = event.get('name', 'Title Not Found')
                date = event.get('event_date', 'Date Not Found')
                ticket_url = event.get('url', 'Ticket URL Not Found')

                show_data = {
                    'title': title,
                    'date': date,
                    'ticket_url': ticket_url
                }
                all_shows.append(show_data)

            except Exception as e:
                print(f"Error extracting show data: {e}")
                continue

        offset += 36

    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        break
    except KeyError as e:
        print(f"KeyError: {e}. Check response structure.")
        break
    except json.JSONDecodeError as e:
        print(f"JSON decoding error: {e}")
        break

for show in all_shows:
    print(f"Title: {show['title']}")
    print(f"Date: {show['date']}")
    print(f"Ticket URL: {show['ticket_url']}")
    print("-" * 20)

print(f"Collected {len(all_shows)} shows.")