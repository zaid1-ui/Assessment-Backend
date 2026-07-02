from fastapi import APIRouter, HTTPException
from app.dependencies import DbSession
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectOut
from app.schemas.common import ApiResponse
from app.services.project_service import ProjectService

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("", response_model=ApiResponse[list[ProjectOut]])
async def list_projects(db: DbSession):
    projects = await ProjectService(db).list_projects()
    return ApiResponse(data=[ProjectOut.model_validate(p) for p in projects])


@router.get("/{project_id}", response_model=ApiResponse[ProjectOut])
async def get_project(project_id: int, db: DbSession):
    project = await ProjectService(db).get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return ApiResponse(data=ProjectOut.model_validate(project))


@router.post("", response_model=ApiResponse[ProjectOut], status_code=201)
async def create_project(payload: ProjectCreate, db: DbSession):
    try:
        project = await ProjectService(db).create_project(payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return ApiResponse(message="Project created", data=ProjectOut.model_validate(project))


@router.patch("/{project_id}", response_model=ApiResponse[ProjectOut])
async def update_project(project_id: int, payload: ProjectUpdate, db: DbSession):
    project = await ProjectService(db).update_project(project_id, payload)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return ApiResponse(message="Project updated", data=ProjectOut.model_validate(project))


@router.delete("/{project_id}", response_model=ApiResponse)
async def delete_project(project_id: int, db: DbSession):
    ok = await ProjectService(db).delete_project(project_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Project not found")
    return ApiResponse(message="Project deleted")
