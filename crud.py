from supabase import create_client, Client
import os

# Load .env file if it exists
from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.orm import Session, selectinload
from extensions import session_factory
from models import Author, Funder, Institution, Paper
from schema import Author as AuthorSchema, Paper as PaperSchema

load_dotenv()


# Replace with your Supabase project URL and API key
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")

# Create a Supabase client
supabase: Client = create_client(supabase_url, supabase_key)


def fuzzy_match_author(name, threshold=0.7):
    print("Threshold:", threshold)  # Print the threshold value
    query = text("SELECT * FROM authors WHERE similarity(name, :name) > :threshold")
    result = session.execute(query, {"name": name, "threshold": threshold}).fetchall()
    if result:
        author = (
            session.query(Author)
            .filter_by(id=result[0].id)
            .options(selectinload(Author.funders), selectinload(Author.institutions))
            .first()
        )
        return author
    return None


def fuzzy_match_funder(name, threshold=0.7):
    with session_factory() as session:
        print("Threshold:", threshold)  # Print the threshold value
        query = text("SELECT * FROM funders WHERE similarity(name, :name) > :threshold")
        result = session.execute(
            query, {"name": name, "threshold": threshold}
        ).fetchall()
        if result:
            funder = session.query(Funder).filter_by(id=result[0].id).first()
            return funder


def fuzzy_match_institution(name, threshold=0.7):
    with session_factory() as session:
        print("Threshold:", threshold)  # Print the threshold value
        query = text(
            "SELECT * FROM institutions WHERE similarity(name, :name) > :threshold"
        )
        result = session.execute(
            query, {"name": name, "threshold": threshold}
        ).fetchall()
        if result:
            institution = session.query(Institution).filter_by(id=result[0].id).first()
            return institution
        return None


def update_database(paper: PaperSchema, author: AuthorSchema):
    with session_factory() as session:
        session: Session

        # DOI lookup of paper
        db_paper = session.query(Paper).filter_by(doi=paper.doi).first()
        if not db_paper:
            db_paper = Paper(doi=paper.doi)
            session.add(db_paper)
            session.commit()
            session.refresh(db_paper)

        # Fuzzy lookup of author
        db_author = fuzzy_match_author(author.name)
        if not db_author:
            db_author = Author(name=author.name)
            session.add(db_author)
            print("Author not found, adding new author to the database")
        else:
            # Merge the existing author instance with the new data
            db_author = session.merge(db_author)
            print(f"Author {db_author} found in the database")

        # Fuzzy match funders
        db_funders = []
        for funder in author.funders:
            funder: Funder
            db_funder = fuzzy_match_funder(funder.name)
            if not db_funder:
                db_funder = Funder(name=funder.name)
                session.add(db_funder)
                print("Funder not found, adding new funder to the database")
            else:
                db_funder = session.merge(db_funder)
                print(f"Funder {db_funder} found in the database")
            db_funders.append(db_funder)

        # Fuzzy match institutions
        db_institutions = []
        for institution in author.institution:
            institution: Institution
            db_institution = fuzzy_match_institution(institution.name)
            if not db_institution:
                db_institution = Institution(name=institution.name)
                session.add(db_institution)
                print("Institution not found, adding new institution to the database")
            else:
                db_institution = session.merge(db_institution)
                print(f"Institution {db_institution} found in the database")
            db_institutions.append(db_institution)

        # Update author with matched institutions and funders
        for institution in db_institutions:
            if institution not in db_author.institutions:
                db_author.institutions.append(institution)
                print(f"Adding {institution} to {db_author}")
        for funder in db_funders:
            if funder not in db_author.funders:
                db_author.funders.append(funder)
                print(f"Adding {funder} to {db_author}")

        # DOI lookup of paper
        db_paper = session.query(Paper).filter_by(doi=paper.doi).first()
        if not db_paper:
            db_paper = Paper(doi=paper.doi)
            session.add(db_paper)

        # Update paper with matched authors and funders
        if db_author not in db_paper.authors:
            db_paper.authors.append(db_author)
        for funder in paper.funders:
            db_funder = fuzzy_match_funder(funder.name)
            if not db_funder:
                db_funder = Funder(name=funder.name)
                session.add(db_funder)
                print("Funder for Paper not found, adding new funder to the database")
            else:
                db_funder = session.merge(db_funder)
                print(f"Funder {db_funder} found in the database")
            if db_funder not in db_paper.funders:
                db_paper.funders.append(db_funder)

        session.add(db_paper, db_author)
        session.commit()
        session.close()
