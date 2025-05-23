"""
Handles Create, Read, Update, Delete (CRUD) operations for the database models.

This module provides functions to interact with the database, such as:
- Matching existing entities (authors, funders, institutions) using case-insensitive exact matching.
  (Note: Original fuzzy matching using `similarity()` was specific to PostgreSQL and has been
  adapted for SQLite compatibility).
- Updating the database with information from parsed paper and author data,
  including creating new entities and establishing relationships.

All database operations are performed within a session managed by `session_factory`
to ensure proper session lifecycle management.
"""
from sqlalchemy.orm import Session, selectinload
from extensions import session_factory
from models import Author, Funder, Institution, Paper, AuthorFunders
from schema import Author as AuthorSchema, Paper as PaperSchema


def fuzzy_match_author(session: Session, name: str, threshold: float = 0.7) -> Optional[Author]:
    """
    Retrieves an author from the database by name using a case-insensitive exact match.

    The 'threshold' parameter is retained for conceptual compatibility with previous
    fuzzy matching logic but is not used in the current SQLite implementation.
    The original fuzzy matching (e.g., using `similarity(name, :name) > :threshold`)
    relied on PostgreSQL-specific functions not available in SQLite.

    Args:
        session: The SQLAlchemy session to use for the query.
        name: The name of the author to match.
        threshold: (Unused in SQLite version) The similarity threshold for a match.

    Returns:
        The matched Author object or None if no match is found.
    """
    # Debug print, consider replacing with actual logging in production
    print(f"Attempting to match author: {name}")
    author = (
        session.query(Author)
        .filter(Author.name.ilike(name)) # Case-insensitive exact match
        .options(
            selectinload(Author.author_funder_associations), # Eager load associations
            selectinload(Author.institutions)                 # Eager load institutions
        )
        .first()
    )
    if author:
        print(f"Found author: {author.name}")
    else:
        print(f"Author not found: {name}")
    return author


def fuzzy_match_funder(session: Session, name: str, threshold: float = 0.7) -> Optional[Funder]:
    """
    Retrieves a funder from the database by name using a case-insensitive exact match.

    Similar to `fuzzy_match_author`, the 'threshold' parameter is unused in this SQLite version.
    The original logic was PostgreSQL-specific.

    Args:
        session: The SQLAlchemy session to use for the query.
        name: The name of the funder to match.
        threshold: (Unused in SQLite version) The similarity threshold for a match.

    Returns:
        The matched Funder object or None if no match is found.
    """
    print(f"Attempting to match funder: {name}")
    funder = session.query(Funder).filter(Funder.name.ilike(name)).first()
    if funder:
        print(f"Found funder: {funder.name}")
    else:
        print(f"Funder not found: {name}")
    return funder


def fuzzy_match_institution(session: Session, name: str, threshold: float = 0.7) -> Optional[Institution]:
    """
    Retrieves an institution from the database by name using a case-insensitive exact match.

    Similar to `fuzzy_match_author`, the 'threshold' parameter is unused in this SQLite version.
    The original logic was PostgreSQL-specific.

    Args:
        session: The SQLAlchemy session to use for the query.
        name: The name of the institution to match.
        threshold: (Unused in SQLite version) The similarity threshold for a match.

    Returns:
        The matched Institution object or None if no match is found.
    """
    print(f"Attempting to match institution: {name}")
    institution = (
        session.query(Institution).filter(Institution.name.ilike(name)).first()
    )
    if institution:
        print(f"Found institution: {institution.name}")
    else:
        print(f"Institution not found: {name}")
    return institution


def update_database(paper: PaperSchema, author: AuthorSchema):
    """
    Updates the database with information from a given paper and its author.

    This function performs the following operations within a single database session:
    1.  Finds or creates the Paper object based on its DOI.
    2.  Finds or creates the Author object based on the author's name.
    3.  Finds or creates Funder objects listed in the author's schema.
    4.  Finds or creates Institution objects listed in the author's schema.
    5.  Associates the author with their institutions.
    6.  Creates AuthorFunders links to associate the author with their funders *for this specific paper*.
    7.  Associates the author with the paper.
    8.  Associates the paper with its direct funders (funders listed at the paper level).
    9.  Commits all changes to the database.

    Args:
        paper (PaperSchema): A Pydantic schema object representing the paper.
        author (AuthorSchema): A Pydantic schema object representing one of the paper's authors.
    """
    with session_factory() as session: # Ensure session is managed and closed properly
        # 1. Find or create the Paper
        db_paper = session.query(Paper).filter_by(doi=paper.doi).first()
        if not db_paper:
            db_paper = Paper(doi=paper.doi)
            session.add(db_paper)
            # Flush to get db_paper.id if it's new and needed for relationships before commit.
            # However, SQLAlchemy often handles this order automatically at commit time.
            # For explicit control, a flush can be used here.
            # session.flush() 
            print(f"Paper with DOI '{paper.doi}' not found, adding new paper.")

        # 2. Find or create the Author
        db_author = fuzzy_match_author(session, author.name)
        if not db_author:
            db_author = Author(name=author.name)
            session.add(db_author)
            print(f"Author '{author.name}' not found, adding new author to the database.")
        else:
            print(f"Author '{db_author.name}' found in the database.")

        # 3. Find or create Funder objects from author's schema
        author_related_funders = []
        for funder_data in author.funders:
            db_funder = fuzzy_match_funder(session, funder_data.name)
            if not db_funder:
                db_funder = Funder(name=funder_data.name)
                session.add(db_funder)
                print(f"Funder '{funder_data.name}' (author-related) not found, adding new funder.")
            else:
                print(f"Funder '{db_funder.name}' (author-related) found in the database.")
            author_related_funders.append(db_funder)

        # 4. Find or create Institution objects from author's schema
        author_related_institutions = []
        for institution_data in author.institution:
            db_institution = fuzzy_match_institution(session, institution_data.name)
            if not db_institution:
                db_institution = Institution(name=institution_data.name)
                session.add(db_institution)
                print(f"Institution '{institution_data.name}' not found, adding new institution.")
            else:
                print(f"Institution '{db_institution.name}' found in the database.")
            author_related_institutions.append(db_institution)

        # 5. Associate author with their institutions
        if db_author.institutions is None: # Should be initialized by SQLAlchemy relationship
            db_author.institutions = []
        for inst_obj in author_related_institutions:
            if inst_obj not in db_author.institutions:
                db_author.institutions.append(inst_obj)
                print(f"Adding institution '{inst_obj.name}' to author '{db_author.name}'.")
        
        # Ensure db_paper.id is available if it's a new paper before creating AuthorFunders
        # A flush might be needed here if db_paper was just created and not yet flushed.
        if db_paper.id is None:
            session.flush() # Ensure db_paper.id is populated

        # 6. Create AuthorFunders links (author -> funder for this specific paper)
        for funder_obj in author_related_funders:
            existing_link = session.query(AuthorFunders).filter_by(
                author_id=db_author.id,
                funder_id=funder_obj.id,
                paper_id=db_paper.id 
            ).first()
            if not existing_link:
                new_link = AuthorFunders(
                    author_id=db_author.id, # Can also use author=db_author
                    funder_id=funder_obj.id, # Can also use funder=funder_obj
                    paper_id=db_paper.id     # Can also use paper=db_paper
                )
                session.add(new_link)
                print(f"Linking author '{db_author.name}' with funder '{funder_obj.name}' for paper '{db_paper.doi}'.")
            else:
                print(f"Link already exists for author '{db_author.name}', funder '{funder_obj.name}', paper '{db_paper.doi}'.")

        # 7. Associate author with the paper
        if db_paper.authors is None: # Should be initialized by SQLAlchemy relationship
            db_paper.authors = []
        if db_author not in db_paper.authors:
            db_paper.authors.append(db_author)
            print(f"Adding author '{db_author.name}' to paper '{db_paper.doi}'.")

        # 8. Associate paper with its direct funders (from paper.funders in schema)
        if paper.funders: # Check if paper.funders list is provided in the schema
            if db_paper.funders is None: # Should be initialized by SQLAlchemy relationship
                db_paper.funders = []
            for paper_funder_data in paper.funders:
                db_paper_funder = fuzzy_match_funder(session, paper_funder_data.name)
                if not db_paper_funder:
                    db_paper_funder = Funder(name=paper_funder_data.name)
                    session.add(db_paper_funder)
                    print(f"Funder '{paper_funder_data.name}' (paper-direct) not found, adding new funder.")
                if db_paper_funder not in db_paper.funders:
                    db_paper.funders.append(db_paper_funder)
                    print(f"Adding funder '{db_paper_funder.name}' directly to paper '{db_paper.doi}'.")
        
        # 9. Commit all changes
        session.commit()
        print(f"Database update committed for paper DOI: {paper.doi} and author: {author.name}.")
from typing import Optional
