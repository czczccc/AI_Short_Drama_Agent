from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.common import ErrorResponse
from app.schemas.project import ProjectCreate, ProjectRead
from app.services import project_service

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post(
    "",
    response_model=ProjectRead,
    status_code=status.HTTP_201_CREATED,
    responses={
        500: {"model": ErrorResponse, "description": "数据库操作失败"},
    },
)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)) -> ProjectRead:
    return project_service.create_project(db, payload)


@router.get(
    "/{project_id}",
    response_model=ProjectRead,
    responses={
        404: {"model": ErrorResponse, "description": "项目不存在"},
        500: {"model": ErrorResponse, "description": "数据库操作失败"},
    },
)
def get_project(project_id: int, db: Session = Depends(get_db)) -> ProjectRead:
    project = project_service.get_project(db, project_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    return project
