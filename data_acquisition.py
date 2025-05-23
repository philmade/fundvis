"""
Handles data acquisition from external APIs, focusing on fetching paper information
from OpenAlex and transforming it into the application's Pydantic schemas.
"""
import requests
from typing import Optional, List, Dict, Any
from pprint import pprint

# Assuming schema.py is in the same directory or accessible in PYTHONPATH
from schema import Paper as PaperSchema, Author as AuthorSchema, Institution as InstitutionSchema, Funder as FunderSchema
# Assuming crud.py is in the same directory or accessible in PYTHONPATH
from crud import update_database
from extensions import engine # For direct DB operations if needed, or session_factory
from sqlalchemy.orm import sessionmaker


# --- OpenAlex API Interaction ---

def fetch_paper_data_from_openalex(doi: str) -> Optional[PaperSchema]:
    """
    Fetches paper data from the OpenAlex API for a given DOI and transforms it
    into a PaperSchema Pydantic model.

    Args:
        doi (str): The Digital Object Identifier of the paper to fetch.
                   It should be provided without the "doi:" prefix.

    Returns:
        Optional[PaperSchema]: A Pydantic PaperSchema object populated with data
                               from OpenAlex, or None if the paper is not found,
                               the DOI is invalid, or an API error occurs.
    """
    if doi.startswith("https://doi.org/"):
        doi = doi.replace("https://doi.org/", "", 1)
    
    api_url = f"https://api.openalex.org/works/doi:{doi}"
    print(f"Fetching data from OpenAlex: {api_url}")

    try:
        response = requests.get(api_url)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4XX or 5XX)
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            print(f"DOI {doi} not found on OpenAlex (404). URL: {api_url}")
        else:
            print(f"HTTP error occurred while fetching DOI {doi}: {e}. URL: {api_url}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Request error occurred while fetching DOI {doi}: {e}. URL: {api_url}")
        return None

    try:
        data = response.json()
    except ValueError: # Includes JSONDecodeError
        print(f"Failed to decode JSON response for DOI {doi}. URL: {api_url}")
        return None

    # --- Transform API Response to Pydantic Schemas ---
    
    # Extract DOI (OpenAlex includes "https://doi.org/" prefix)
    extracted_doi = data.get("doi")
    if extracted_doi and extracted_doi.startswith("https://doi.org/"):
        extracted_doi = extracted_doi.replace("https://doi.org/", "", 1)
    else: # Fallback if DOI format is unexpected or missing
        extracted_doi = doi 

    # Extract Authors and their affiliations/funders
    authors_schemas: List[AuthorSchema] = []
    for author_data in data.get("authorships", []):
        author_info = author_data.get("author", {})
        author_name = author_info.get("display_name")
        if not author_name:
            continue # Skip if author name is missing

        # Extract Institutions
        institutions_schemas: List[InstitutionSchema] = []
        for affiliation_data in author_data.get("institutions", []):
            institution_name = affiliation_data.get("display_name")
            if institution_name:
                institutions_schemas.append(InstitutionSchema(name=institution_name))

        # Extract Funders associated with this author through grants for this paper
        # OpenAlex's primary way of linking funders is through "grants" on the work object.
        # Each grant lists funders. We are trying to associate these funders with authors.
        # This is an approximation; OpenAlex doesn't directly link grants to specific authorships.
        # For simplicity, we'll associate all paper-level funders (from grants) with each author.
        # A more nuanced approach might be needed if author-specific funding is critical.
        author_funders_schemas: List[FunderSchema] = []
        for grant in data.get("grants", []):
            funder_name = grant.get("funder_display_name") # OpenAlex grant structure
            if funder_name and not any(f.name == funder_name for f in author_funders_schemas): # Avoid duplicates for this author
                author_funders_schemas.append(FunderSchema(name=funder_name))
        
        authors_schemas.append(AuthorSchema(
            name=author_name,
            institution=institutions_schemas,
            funders=author_funders_schemas # All paper funders attributed to each author for now
        ))

    # Extract Paper-level Funders (these are the same funders from grants)
    paper_funders_schemas: List[FunderSchema] = []
    for grant in data.get("grants", []):
        funder_name = grant.get("funder_display_name")
        if funder_name and not any(f.name == funder_name for f in paper_funders_schemas): # Avoid duplicates
            paper_funders_schemas.append(FunderSchema(name=funder_name))
            
    # Create PaperSchema instance
    paper_schema = PaperSchema(
        doi=extracted_doi,
        authors=authors_schemas,
        funders=paper_funders_schemas
    )

    return paper_schema


# --- Database Interaction ---

def add_paper_to_db(paper_schema: PaperSchema):
    """
    Adds a paper and its associated authors, institutions, and funders
    to the database using the `crud.update_database` function.

    Args:
        paper_schema (PaperSchema): The Pydantic schema object for the paper.
    """
    if not paper_schema:
        print("No paper data to add to DB.")
        return

    print(f"\nAdding paper DOI: {paper_schema.doi} to the database...")
    if not paper_schema.authors:
        print(f"Paper {paper_schema.doi} has no authors listed. Skipping database update for authors.")
        # Optionally, one might still want to record the paper itself, or its direct funders,
        # even if no authors are listed. Current crud.update_database requires an author.
        # For now, if no authors, we effectively don't add the paper via this function.
        # A separate function in crud.py might be needed to add a paper without authors,
        # or to only update paper-level funders.
        return

    for author_schema in paper_schema.authors:
        print(f"Processing author: {author_schema.name} for paper {paper_schema.doi}")
        try:
            update_database(paper_schema, author_schema)
            print(f"Successfully processed and initiated update for author '{author_schema.name}' and paper '{paper_schema.doi}'.")
        except Exception as e:
            print(f"Error updating database for author '{author_schema.name}' and paper '{paper_schema.doi}': {e}")
            # Potentially re-raise or handle more gracefully depending on requirements


# --- Example Usage ---

if __name__ == "__main__":
    # Test DOI - Example: "10.1016/S2213-2600(23)00083-8" (from real.json)
    # Another example: "10.1038/s41586-021-03491-6" (Nature paper on AlphaFold)
    test_doi = "10.1038/s41586-021-03491-6" 
    
    print(f"--- Attempting to fetch paper data for DOI: {test_doi} ---")
    paper_data_schema = fetch_paper_data_from_openalex(test_doi)

    if paper_data_schema:
        print("\n--- Fetched Paper Data (Pydantic Schema) ---")
        pprint(paper_data_schema.dict()) # .dict() for better pprint of Pydantic models

        print("\n--- Adding fetched paper to database ---")
        # Note: This will interact with your actual database as configured in extensions.py
        # Ensure your database is set up and `crud.update_database` works as expected.
        add_paper_to_db(paper_data_schema)
        print("\n--- Database addition process finished ---")
    else:
        print(f"\n--- Could not fetch paper data for DOI: {test_doi} ---")

    # Example of a DOI that might not exist or have limited info
    # test_doi_not_found = "10.9999/nonexistent-doi-12345"
    # print(f"\n--- Attempting to fetch paper data for potentially non-existent DOI: {test_doi_not_found} ---")
    # paper_data_not_found = fetch_paper_data_from_openalex(test_doi_not_found)
    # if paper_data_not_found:
    #     pprint(paper_data_not_found.dict())
    #     add_paper_to_db(paper_data_not_found)
    # else:
    #     print(f"--- Could not fetch paper data for DOI: {test_doi_not_found} ---")
