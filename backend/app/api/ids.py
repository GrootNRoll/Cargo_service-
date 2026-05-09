from typing import Annotated

from fastapi import Path

from app.constants import MAX_DB_INTEGER

DbPathId = Annotated[int, Path(ge=1, le=MAX_DB_INTEGER)]
