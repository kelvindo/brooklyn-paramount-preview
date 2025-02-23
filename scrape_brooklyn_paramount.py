import requests
from bs4 import BeautifulSoup

def scrape_brooklyn_paramount_shows():
    """
    Scrapes the Brooklyn Paramount shows site and extracts show information.

    Returns:
        A list of dictionaries, where each dictionary represents a show
        and contains the show's title, date, and ticket URL.
        Returns an empty list if there's an error fetching or parsing the page.
    """

    url = "https://www.brooklynparamount.com/shows"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL: {e}")
        return []

    soup = BeautifulSoup(response.content, 'html.parser')
    shows = []

    # Find all show elements. The selector might need adjustment if the website changes.
    show_elements = soup.find_all('div', class_='chakra-card__footer')

    for show_element in show_elements:
        try:
            # Extract show title
            title_element = show_element.find('p', class_='css-zvlevn')
            title = title_element.text.strip() if title_element else "Title Not Found"

            # Extract show date
            date_element = show_element.find('p', class_='css-5f5os7')
            date = date_element.text.strip() if date_element else "Date Not Found"

            # Extract ticket URL (find the 'Buy Tickets' link)
            ticket_link_element = show_element.find('a', class_='css-ipgcik')
            ticket_url = ticket_link_element['href'] if ticket_link_element and ticket_link_element.has_attr('href') else "Ticket URL Not Found"


            show_data = {
                'title': title,
                'date': date,
                'ticket_url': ticket_url
            }
            shows.append(show_data)

        except Exception as e:
            print(f"Error parsing show element: {e}")
            # You could log the specific show_element causing the error here if needed.
            continue  # Continue to the next show, even if one fails

    return shows



def main():
    """
    Main function to scrape show data and print it.
    """
    shows = scrape_brooklyn_paramount_shows()

    if shows:
        for show in shows:
            print(f"Title: {show['title']}")
            print(f"Date: {show['date']}")
            print(f"Ticket URL: {show['ticket_url']}")
            print("-" * 20)
    else:
        print("No shows found or error during scraping.")


if __name__ == "__main__":
    main()