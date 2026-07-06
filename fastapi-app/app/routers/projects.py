from fastapi import APIRouter, HTTPException
from app.dependencies import CurrentUserId, DbSession
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectOut
from app.schemas.common import ApiResponse
from app.services.project_service import ProjectService

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("", response_model=ApiResponse[list[ProjectOut]])
async def list_projects(db: DbSession, user_id: CurrentUserId):
    """Only the logged-in user's own projects."""
    projects = await ProjectService(db).list_projects(owner_id=user_id)
    return ApiResponse(data=[ProjectOut.model_validate(p) for p in projects])


@router.get("/{project_id}", response_model=ApiResponse[ProjectOut])
async def get_project(project_id: int, db: DbSession, user_id: CurrentUserId):
    project = await ProjectService(db).get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.owner_id != user_id:
        raise HTTPException(status_code=403, detail="You do not own this project")
    return ApiResponse(data=ProjectOut.model_validate(project))


@router.post("", response_model=ApiResponse[ProjectOut], status_code=201)
async def create_project(payload: ProjectCreate, db: DbSession, user_id: CurrentUserId):
    # Owner comes from the session, never from the request body.
    project = await ProjectService(db).create_project(payload, owner_id=user_id)
    return ApiResponse(message="Project created", data=ProjectOut.model_validate(project))


@router.patch("/{project_id}", response_model=ApiResponse[ProjectOut])
async def update_project(project_id: int, payload: ProjectUpdate,
                         db: DbSession, user_id: CurrentUserId):
    service = ProjectService(db)
    project = await service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.owner_id != user_id:
        raise HTTPException(status_code=403, detail="You do not own this project")
    project = await service.update_project(project_id, payload)
    return ApiResponse(message="Project updated", data=ProjectOut.model_validate(project))


@router.delete("/{project_id}", response_model=ApiResponse)
async def delete_project(project_id: int, db: DbSession, user_id: CurrentUserId):
    service = ProjectService(db)
    project = await service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.owner_id != user_id:
        raise HTTPException(status_code=403, detail="You do not own this project")
    await service.delete_project(project_id)
    return ApiResponse(message="Project deleted")
