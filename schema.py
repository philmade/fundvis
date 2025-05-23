"""
Defines Pydantic models for data validation and serialization.

These models are used to represent the structure of incoming data (e.g., from JSON files)
and to ensure that the data conforms to expected types and structures before being
processed or stored in the database. They serve as a data interface layer.
"""
from pydantic import BaseModel
from typing import List, Optional # Optional can be used if some fields are not always present

class Institution(BaseModel):
    """
    Pydantic model for an Institution.

    Attributes:
        name (str): The name of the institution.
    """
    name: str

    class Config:
        """Pydantic config for ORM mode, allowing model to be created from ORM objects."""
        orm_mode = True


class Funder(BaseModel):
    """
    Pydantic model for a Funder.

    Attributes:
        name (str): The name of the funder.
    """
    name: str

    class Config:
        """Pydantic config for ORM mode."""
        orm_mode = True


class Author(BaseModel):
    """
    Pydantic model for an Author.

    Attributes:
        name (str): The name of the author.
        institution (List[Institution]): A list of institutions associated with the author.
        funders (List[Funder]): A list of funders associated with the author.
    """
    name: str
    institution: List[Institution] # Represents the author's affiliated institutions
    funders: List[Funder]         # Represents funders directly linked to the author's work or conflicts

    class Config:
        """Pydantic config for ORM mode."""
        orm_mode = True


class Paper(BaseModel):
    """
    Pydantic model for a Paper.

    Attributes:
        doi (str): The Digital Object Identifier of the paper.
        authors (Optional[List[Author]]): An optional list of authors of the paper.
        funders (Optional[List[Funder]]): An optional list of funders for the paper.
                                          These are general funders for the paper itself.
    """
    doi: str
    authors: Optional[List[Author]] = None # Authors might not always be provided initially
    funders: Optional[List[Funder]] = None # Funders might not always be provided initially

    class Config:
        """Pydantic config for ORM mode."""
        orm_mode = True
