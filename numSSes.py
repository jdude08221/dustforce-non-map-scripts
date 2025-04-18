import requests
import argparse
import sys

# Function to count "scores" entries with specific criteria
def count_scores(map_name_id):
    base_url = "https://dustkid.com/json/level"
    level_name, level_id = map_name_id.rsplit("-", 1)
    full_level_name = f"{level_name}-{level_id}"
    start_index = 0
    step = 50
    total_entries = 0

    while True:
        url = f"{base_url}/{full_level_name}/all/{start_index}"
        response = requests.get(url)

        if response.status_code != 200:
            print(f"Failed to fetch page {start_index} for level '{full_level_name}'. HTTP status code: {response.status_code}", flush=True)
            break

        data = response.json()
        scores = data.get("scores", {})

        # Count entries where both score_completion and score_finesse are 5
        filtered_scores = [
            entry for entry in scores.values()
            if entry.get("score_completion") == 5 and entry.get("score_finesse") == 5
        ]
        total_entries += len(filtered_scores)

        if len(scores) == 0:
            break

        print(f"Level '{full_level_name}', Page {start_index}: {len(filtered_scores)} filtered entries found.", flush=True)
        start_index += step

    print(f"Number of SSes for level '{full_level_name}': {total_entries}", flush=True)
    return total_entries

# Main script
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Count filtered scores for multiple maps")
    parser.add_argument("maps", nargs="+", type=str, help="List of formatted map names and IDs (e.g., Forest-Best-Hub-13181)")
    args = parser.parse_args()

    # Aggregate total entries across all maps
    total_entries_across_maps = 0
    for map_entry in args.maps:  # args.maps should contain all arguments as a list
        print(f"Processing map: {map_entry}", flush=True)  # Debug log
        map_total = count_scores(map_entry)
        total_entries_across_maps += map_total

    # Output the final total count
    print(f"Number of SSes: {total_entries_across_maps}", flush=True)