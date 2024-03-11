from typing import List
from sqlalchemy import Column, Integer, String, ForeignKey, Table
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class Institution(Base):
    __tablename__ = "institutions"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    authors = relationship(
        "Author", secondary="author_institutions", back_populates="institutions"
    )
    funders = relationship(
        "Funder", secondary="institution_funders", back_populates="institutions"
    )


class Funder(Base):
    __tablename__ = "funders"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    institutions = relationship(
        "Institution", secondary="institution_funders", back_populates="funders"
    )
    papers = relationship("Paper", secondary="paper_funders", back_populates="funders")


class Author(Base):
    __tablename__ = "authors"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    institutions = relationship(
        "Institution", secondary="author_institutions", back_populates="authors"
    )
    papers = relationship("Paper", secondary="paper_authors", back_populates="authors")
    funders = relationship("Funder", secondary="author_funders")


class AuthorFunders(Base):
    __tablename__ = "author_funders"
    author_id = Column(Integer, ForeignKey("authors.id"), primary_key=True)
    funder_id = Column(Integer, ForeignKey("funders.id"), primary_key=True)
    paper_id = Column(Integer, ForeignKey("papers.id"), primary_key=True)


class Paper(Base):
    __tablename__ = "papers"
    id = Column(Integer, primary_key=True)
    doi = Column(String)
    authors = relationship("Author", secondary="paper_authors", back_populates="papers")
    funders = relationship("Funder", secondary="paper_funders", back_populates="papers")


institution_funders = Table(
    "institution_funders",
    Base.metadata,
    Column("institution_id", Integer, ForeignKey("institutions.id"), primary_key=True),
    Column("funder_id", Integer, ForeignKey("funders.id"), primary_key=True),
)

author_institutions = Table(
    "author_institutions",
    Base.metadata,
    Column("author_id", Integer, ForeignKey("authors.id"), primary_key=True),
    Column("institution_id", Integer, ForeignKey("institutions.id"), primary_key=True),
)

paper_authors = Table(
    "paper_authors",
    Base.metadata,
    Column("paper_id", Integer, ForeignKey("papers.id"), primary_key=True),
    Column("author_id", Integer, ForeignKey("authors.id"), primary_key=True),
)

paper_funders = Table(
    "paper_funders",
    Base.metadata,
    Column("paper_id", Integer, ForeignKey("papers.id"), primary_key=True),
    Column("funder_id", Integer, ForeignKey("funders.id"), primary_key=True),
)
