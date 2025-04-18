import requests
from bs4 import BeautifulSoup
import argparse

# Function to retrieve and format map names and IDs
def fetch_maps(tag):
    base_url = f"http://atlas.dustforce.com/tag/{tag}"
    start_index = 0
    step = 10
    formatted_maps = []

    while True:
        url = f"{base_url}?start={start_index}"
        response = requests.get(url)

        if response.status_code != 200:
            print(f"Failed to fetch page {start_index}. HTTP status code: {response.status_code}")
            break

        soup = BeautifulSoup(response.content, "html.parser")
        map_elements = soup.find_all(class_="map-page-list")

        if not map_elements:
            break

        for map_element in map_elements:
            # Find the link within the map element
            link = map_element.find("a", class_="dark-link")
            if link:
                name = link.text.strip()  # Get the text inside the <a> tag
                href = link.get("href")  # Get the href attribute
                # Replace spaces with hyphens in the map name
                formatted_name = name.replace(" ", "-")
                # Extract the ID from the href attribute and concatenate it
                if href:
                    parts = href.strip("../").split("/")
                    if len(parts) >= 1:
                        map_id = parts[0]
                        formatted_maps.append(f"{formatted_name}-{map_id}")

        #print(f"Page {start_index}: Processed {len(map_elements)} maps.")
        start_index += step

    return formatted_maps

# Main script
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch map names and IDs for a given tag")
    parser.add_argument("tag", type=str, help="The tag name (e.g., dlc-8)")
    args = parser.parse_args()

    maps = fetch_maps(args.tag)
    for map_entry in maps:
        print(map_entry)