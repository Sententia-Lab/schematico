from typing import Annotated
from pydantic import Field

UrlArg = Annotated[
    str, Field(pattern=r"^(https?)://", description="Absolute http or https URL")
]
