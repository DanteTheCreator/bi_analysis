from pydantic import BaseModel, Field
from typing import List

from llama_index.program.lmformatenforcer import (
    LMFormatEnforcerPydanticProgram,
)

class Song(BaseModel):
    title: str
    length_seconds: int


class Album(BaseModel):
    name: str
    artist: str
    songs: List[Song] = Field(min_items=3, max_items=10)
    
    from llama_index.llms.llama_cpp import LlamaCPP

llm = LlamaCPP()

program = LMFormatEnforcerPydanticProgram(
    output_cls=Album,
    prompt_template_str=(
        "Your response should be according to the following json schema: \n"
        "{json_schema}\n"
        "Generate an example album, with an artist and a list of songs. Using"
        " the movie {movie_name} as inspiration. "
    ),
    llm=llm,
    verbose=True,
)

output = program(movie_name="The Shining")
