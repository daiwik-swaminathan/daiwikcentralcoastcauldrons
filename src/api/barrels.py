from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)

class Barrel(BaseModel):
    sku: str

    ml_per_barrel: int
    potion_type: list[int]
    price: int

    quantity: int

@router.post("/deliver")
def post_deliver_barrels(barrels_delivered: list[Barrel]):
    """ """
    print(barrels_delivered)

    ml_in_barrels = 0
    gold = 0
    with db.engine.begin() as connection:

        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        first_row = result.first()

        ml_in_barrels = first_row.num_red_ml
        gold = first_row.gold

        gold -= barrels_delivered[0].price
        ml_in_barrels += barrels_delivered[0].ml_per_barrel

        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_ml = {ml_in_barrels}"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold = {gold}"))

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)

    # Is it guaranteed that if a SMALL_RED_BARREL is in the barrel catalog
    # that the quantity is at least 1?

    return [
        {
            "sku": "SMALL_RED_BARREL",
            "quantity": 1,
        }
    ]
