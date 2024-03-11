import json
from crud import update_database
from schema import Paper, Author
from pprint import pprint

# Load the JSON data
with open("real.json") as file:
    json_data = json.load(file)

# Parse the JSON data into Pydantic models
authors = [Author(**author_data) for author_data in json_data[0]["authors"]]
paper = Paper(doi=json_data[0]["doi"], authors=authors, funders=json_data[0]["funders"])
# Update the database
for author in authors:
    update_database(paper, author)
