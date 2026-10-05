from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from club_service.infrastructure.database import get_session

SessionDependency = Annotated[Session, Depends(get_session)]
