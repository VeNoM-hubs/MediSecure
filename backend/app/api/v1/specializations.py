from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession, require_roles
from app.core.rbac import Role
from app.models.specialization import Specialization
from app.models.user import User
from app.schemas.common import SpecializationCreate, SpecializationOut
from app.services.audit import write_audit

router = APIRouter()


@router.get("", response_model=list[SpecializationOut])
def list_specializations(db: DbSession, user: CurrentUser) -> list[SpecializationOut]:
    specs = db.scalars(select(Specialization).order_by(Specialization.name)).all()
    return [SpecializationOut.model_validate(s) for s in specs]


@router.post("", response_model=SpecializationOut, status_code=status.HTTP_201_CREATED)
def create_specialization(
    payload: SpecializationCreate,
    db: DbSession,
    admin: User = Depends(require_roles(Role.ADMIN)),
) -> SpecializationOut:
    existing = db.scalar(select(Specialization).where(Specialization.name == payload.name))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Specialization already exists")
    spec = Specialization(name=payload.name, description=payload.description)
    db.add(spec)
    write_audit(
        db,
        action="specialization.create",
        actor=admin,
        resource_type="specialization",
        resource_id=spec.id,
    )
    db.commit()
    db.refresh(spec)
    return SpecializationOut.model_validate(spec)


@router.delete("/{spec_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_specialization(
    spec_id: str,
    db: DbSession,
    admin: User = Depends(require_roles(Role.ADMIN)),
) -> None:
    spec = db.get(Specialization, spec_id)
    if not spec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    write_audit(
        db,
        action="specialization.delete",
        actor=admin,
        resource_type="specialization",
        resource_id=spec_id,
    )
    db.delete(spec)
    db.commit()
