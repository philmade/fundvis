from pydantic import BaseModel
from typing import List


class Institution(BaseModel):
    name: str


class Funder(BaseModel):
    name: str


class Author(BaseModel):
    name: str
    institution: List[Institution]
    funders: List[Funder]


class Paper(BaseModel):
    doi: str
    authors: List[Author] = None
    funders: List[Funder] = None
