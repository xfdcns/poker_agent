"""牌桌路由 /api/table"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.config.db_conf import get_db
from app.crud.table import get_table_by_id_and_user
from app.crud.action import get_actions_by_table
from app.services.table_service import create_table_service, start_game_service
from app.utils.auth import get_current_user
from app.utils.response import success
from app.schemas.table import CreateTableRequest, StartGameRequest
from app.models.user import User
from fastapi.encoders import jsonable_encoder
import json

router = APIRouter(prefix="/api/table", tags=["牌桌"])


@router.post("/create")
async def create_table(req: CreateTableRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    opponents = [o.model_dump() for o in req.opponents] if req.opponents else None
    data = await create_table_service(
        db=db, user_id=user.id, num_players=req.num_players,
        my_position=req.my_position, my_hole_cards=req.my_hole_cards,
        my_stack=req.my_stack, opponents=opponents,
    )
    return success(data, message="牌桌创建成功")


@router.post("/start")
async def start_game(req: StartGameRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    data = await start_game_service(db=db, table_id=req.table_id, user_id=user.id)
    if not data:
        raise HTTPException(status_code=404, detail="牌桌不存在")
    if "error" in data:
        raise HTTPException(status_code=400, detail=data["error"])
    return success(data, message="游戏开始")


@router.get("/{table_id}")
async def get_table_status(table_id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    table = await get_table_by_id_and_user(db, table_id, user.id)
    if not table:
        raise HTTPException(status_code=404, detail="牌桌不存在")

    actions = await get_actions_by_table(db, table_id)
    opponents = []
    if table.opponents_info:
        try:
            opponents = json.loads(table.opponents_info)
        except Exception:
            opponents = []

    return success({
        "table_id": table.id,
        "num_players": table.num_players,
        "my_position": table.my_position,
        "my_hole_cards": table.my_hole_cards,
        "my_stack": float(table.my_stack),
        "community_cards": table.community_cards,
        "pot_size": float(table.pot_size),
        "status": table.status,
        "current_stage": table.status if table.status not in ("waiting", "settled") else None,
        "opponents": opponents,
        "actions_history": jsonable_encoder(actions),
    })


@router.get("/{table_id}/history")
async def get_table_history(table_id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    table = await get_table_by_id_and_user(db, table_id, user.id)
    if not table:
        raise HTTPException(status_code=404, detail="牌桌不存在")

    actions = await get_actions_by_table(db, table_id)
    return success({"table_id": table_id, "actions": jsonable_encoder(actions)})
