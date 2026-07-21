from sqlalchemy.orm import Session

from app.models.project import Project
from app.schemas.project import ProjectCreate


def create_project(db: Session, data: ProjectCreate) -> Project:
    project = Project(name=data.name, status="draft")
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def get_project(db: Session, project_id: int) -> Project | None:
    return db.get(Project, project_id)
