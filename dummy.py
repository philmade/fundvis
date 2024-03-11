import json
from crud import update_database
from schema import Paper

# Load the JSON data
with open("test.json") as file:
    json_data = json.load(file)

# Parse the JSON data into Pydantic models
papers = [Paper(**paper_data) for paper_data in json_data]

# Update the database
for paper in papers:
    for author in paper.authors:
        update_database(paper, author)
