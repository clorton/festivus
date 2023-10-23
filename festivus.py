#! /usr/bin/env python3

"""Festivus: A Python CLI for the Rest of Us"""

from html.parser import HTMLParser
import json
from pathlib import Path
import click
import pandas as pd
import requests


class OptionParser(HTMLParser):

    """Parse <option> tags from HTML"""

    def __init__(self):
        super().__init__()
        self.parsing_option = False
        self.value = None
        self.team = None
        return

    def handle_starttag(self, tag, attrs):
        if tag == "option":
            self.parsing_option = True
            for attribute in attrs:
                if attribute[0] == "value":
                    self.value = attribute[1]

    def handle_data(self, data: str) -> None:
        if self.parsing_option and data.strip() == "Female/Male Masters 45+":
            self.team = self.value
        return super().handle_data(data)
    
    def handle_endtag(self, tag: str) -> None:
        self.parsing_option = False
        return super().handle_endtag(tag)


@click.command()
@click.option("--getboxes", "getBoxes", default=False, help="Get list of boxes.")
@click.option("--getresults", "getResults", default=False, help="Get list of results.")
def main(getBoxes: bool, getResults: bool):

    """Festivus: A Python CLI for the Rest of Us"""

    print("Hello, Festivus!")

    if getBoxes:
        print("Getting boxes...")
        req = requests.get("https://competitioncorner.net/Event/GetFilteredEvents?timing=past&page=1&perPage=256", timeout=10)
        print(f"{req.status_code=}")
        with Path("data/boxes.json").open("wt") as f:
            f.write(req.text)
        print("Got boxes!")

    with Path("data/boxes.json").open("rt") as f:
        boxes = json.load(f)
        print(f"{len(boxes)=}")

    festivus = list(filter(lambda x: "Festivus" in x["name"], boxes))

    print(f"{len(festivus)=}")

    results = []

    if getResults:
        for f in festivus:

            # Example leaderboard URL: https://competitioncorner.net/ff/10442/results
            # Get HTML for the leaderboard page
            req = requests.get(f["leaderboardUrl"], timeout=10)
            print(f"{f['name']}: {req.status_code=}")
            if req.status_code == 200:
                parser = OptionParser()
                parser.feed(req.text)
                print(f"{parser.team=}")

                if parser.team:

                    team = parser.team[1:]
                    print(f"{team=}")

                    # Example API URL: https://competitioncorner.net/api2/v1/leaderboard/10442/tab/team_65032?start=0&end=50
                    box = f["leaderboardUrl"].split("/")[4]
                    resultsUrl = f"https://competitioncorner.net/api2/v1/leaderboard/{box}/tab/{team}?start=0&end=50"
                    req = requests.get(resultsUrl, timeout=10)
                    print(f"{f['name']}: {req.status_code=}")
                    if req.status_code == 200:
                        results.append(req.json())
                        with Path(f"data/{f['name'].strip().replace('/', '-')}.json").open("wt") as f:
                            f.write(req.text)

                else:
                    print(f"Didn't find a team for 'Female/Male Masters 45+' for {f['name']}")
    else:
        # Load from disk
        for f in festivus:
            path = Path(f"data/{f['name'].strip().replace('/', '-')}.json")
            if path.exists():
                with path.open("rt") as f:
                    results.append(json.load(f))

    print(f"{len(results)=}")

    scores = []

    for box in results:

        workout_map = {w["key"]: w["name"] for w in box["workouts"]}
        
        for athlete in box["athletes"]:
            collected = [("name", athlete["name"]), ("affiliate", athlete["affiliate"])]
            collected.extend([(workout_map[workout], data["res"]) for workout, data in athlete["workoutScores"].items()])
            scores.append(collected)

    print(f"{len(scores)=}")

    columns = set()
    for score in scores:
        for entry in score:
            columns.add(entry[0])

    print(f"{columns=}")



    df = pd.DataFrame([{k:v for k,v in entry} for entry in [score for score in scores]], columns=["name", "affiliate", "Hoppin' and Poppin'!", "3-1-2? It's So Complex!", "Toss it, I'm Over It! (Row)", "Toss it, I'm Over It! (Metcon)", "Get on Up 'n Git Down"])
    df.to_csv("scores.csv", index=False)

    return


if __name__ == "__main__":
    main()
