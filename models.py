"""
Defines the SQLAlchemy ORM models for the application.

This module includes definitions for:
- Institution: Represents an academic or research institution.
- Funder: Represents an organization that funds research.
- Author: Represents a researcher or author of a paper.
- AuthorFunders: An association object linking authors, funders, and papers,
                 representing a specific funding relationship for a specific paper by an author.
- Paper: Represents a published research paper.

It also defines intermediary association tables for many-to-many relationships
that do not require additional attributes (e.g., `institution_funders`, 
`author_institutions`, `paper_authors`, `paper_funders`).

The `Base` is a declarative base for SQLAlchemy model definitions.
"""
from typing import List
from sqlalchemy import Column, Integer, String, ForeignKey, Table
from sqlalchemy.orm import relationship, declarative_base

# Declarative base for SQLAlchemy models
Base = declarative_base()


class Institution(Base):
    """
    Represents a research institution.

    Attributes:
        id (int): Primary key.
        name (str): Name of the institution.
        authors (relationship): Many-to-many relationship with Author through `author_institutions` table.
        funders (relationship): Many-to-many relationship with Funder through `institution_funders` table.
    """
    __tablename__ = "institutions"
    id = Column(Integer, primary_key=True)
    name = Column(String)

    # Many-to-many relationship: Institution <-> Author
    authors = relationship(
        "Author", secondary="author_institutions", back_populates="institutions"
    )
    # Many-to-many relationship: Institution <-> Funder
    funders = relationship(
        "Funder", secondary="institution_funders", back_populates="institutions"
    )


class Funder(Base):
    """
    Represents a funding organization.

    Attributes:
        id (int): Primary key.
        name (str): Name of the funder.
        institutions (relationship): Many-to-many relationship with Institution through `institution_funders` table.
        papers (relationship): Many-to-many relationship with Paper through `paper_funders` table.
        author_funder_associations (relationship): One-to-many relationship with AuthorFunders,
                                                   linking this funder to specific author-paper funding instances.
    """
    __tablename__ = "funders"
    id = Column(Integer, primary_key=True)
    name = Column(String)

    # Many-to-many relationship: Funder <-> Institution
    institutions = relationship(
        "Institution", secondary="institution_funders", back_populates="funders"
    )
    # Many-to-many relationship: Funder <-> Paper
    papers = relationship("Paper", secondary="paper_funders", back_populates="funders")
    # One-to-many relationship: Funder -> AuthorFunders (association object)
    author_funder_associations = relationship("AuthorFunders", back_populates="funder")


class Author(Base):
    """
    Represents an author of a research paper.

    Attributes:
        id (int): Primary key.
        name (str): Name of the author.
        institutions (relationship): Many-to-many relationship with Institution through `author_institutions` table.
        papers (relationship): Many-to-many relationship with Paper through `paper_authors` table.
        author_funder_associations (relationship): One-to-many relationship with AuthorFunders,
                                                   linking this author to specific funder-paper funding instances.
    """
    __tablename__ = "authors"
    id = Column(Integer, primary_key=True)
    name = Column(String)

    # Many-to-many relationship: Author <-> Institution
    institutions = relationship(
        "Institution", secondary="author_institutions", back_populates="authors"
    )
    # Many-to-many relationship: Author <-> Paper
    papers = relationship("Paper", secondary="paper_authors", back_populates="authors")
    # One-to-many relationship: Author -> AuthorFunders (association object)
    # This replaces a direct many-to-many to Funders to include Paper context.
    author_funder_associations = relationship("AuthorFunders", back_populates="author")


class AuthorFunders(Base):
    """
    Association object representing the link between an Author, a Funder, and a Paper.
    This table explicitly stores that a particular author's involvement in a paper
    was funded by a specific funder.

    Attributes:
        author_id (int): Foreign key to authors.id, part of composite primary key.
        funder_id (int): Foreign key to funders.id, part of composite primary key.
        paper_id (int): Foreign key to papers.id, part of composite primary key.
        author (relationship): Many-to-one relationship back to Author.
        funder (relationship): Many-to-one relationship back to Funder.
        paper (relationship): Many-to-one relationship back to Paper.
    """
    __tablename__ = "author_funders"
    author_id = Column(Integer, ForeignKey("authors.id"), primary_key=True)
    funder_id = Column(Integer, ForeignKey("funders.id"), primary_key=True)
    paper_id = Column(Integer, ForeignKey("papers.id"), primary_key=True)

    # Relationships to parent tables for easy access from the association object
    author = relationship("Author", back_populates="author_funder_associations")
    funder = relationship("Funder", back_populates="author_funder_associations")
    paper = relationship("Paper", back_populates="author_funder_associations")


class Paper(Base):
    """
    Represents a research paper.

    Attributes:
        id (int): Primary key.
        doi (str): Digital Object Identifier for the paper.
        authors (relationship): Many-to-many relationship with Author through `paper_authors` table.
        funders (relationship): Many-to-many relationship with Funder through `paper_funders` table
                                (representing general paper funding, not author-specific).
        author_funder_associations (relationship): One-to-many relationship with AuthorFunders,
                                                   linking this paper to specific author-funder instances.
    """
    __tablename__ = "papers"
    id = Column(Integer, primary_key=True)
    doi = Column(String) # Digital Object Identifier

    # Many-to-many relationship: Paper <-> Author
    authors = relationship("Author", secondary="paper_authors", back_populates="papers")
    # Many-to-many relationship: Paper <-> Funder (direct paper funding)
    funders = relationship("Funder", secondary="paper_funders", back_populates="papers")
    # One-to-many relationship: Paper -> AuthorFunders (association object)
    author_funder_associations = relationship("AuthorFunders", back_populates="paper")


# Association table for the many-to-many relationship between Institution and Funder
institution_funders = Table(
    "institution_funders",
    Base.metadata,
    Column("institution_id", Integer, ForeignKey("institutions.id"), primary_key=True),
    Column("funder_id", Integer, ForeignKey("funders.id"), primary_key=True),
)

# Association table for the many-to-many relationship between Author and Institution
author_institutions = Table(
    "author_institutions",
    Base.metadata,
    Column("author_id", Integer, ForeignKey("authors.id"), primary_key=True),
    Column("institution_id", Integer, ForeignKey("institutions.id"), primary_key=True),
)

# Association table for the many-to-many relationship between Paper and Author
paper_authors = Table(
    "paper_authors",
    Base.metadata,
    Column("paper_id", Integer, ForeignKey("papers.id"), primary_key=True),
    Column("author_id", Integer, ForeignKey("authors.id"), primary_key=True),
)

# Association table for the many-to-many relationship between Paper and Funder
# This represents funders directly associated with a paper, not necessarily through a specific author.
paper_funders = Table(
    "paper_funders",
    Base.metadata,
    Column("paper_id", Integer, ForeignKey("papers.id"), primary_key=True),
    Column("funder_id", Integer, ForeignKey("funders.id"), primary_key=True),
)
