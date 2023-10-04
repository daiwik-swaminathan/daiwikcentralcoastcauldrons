from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)

class PotionInventory(BaseModel):
    potion_type: list[int]
    quantity: int

@router.post("/deliver")
def post_deliver_bottles(potions_delivered: list[PotionInventory]):
    """ """
    print(potions_delivered)

    ml_in_barrels = 0
    num_red_potions = 0
    with db.engine.begin() as connection:

        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        first_row = result.first()

        ml_in_barrels = first_row.num_red_ml
        num_red_potions = first_row.num_red_potions

        num_red_potions += potions_delivered[0].quantity
        ml_in_barrels -= 100 * potions_delivered[0].quantity

        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_ml = {ml_in_barrels}"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_potions = {num_red_potions}"))

    return "OK"

# Gets called 4 times a day
@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """

    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    # Initial logic: bottle all barrels into red potions.

    ml_in_barrels = 0
    num_potions_to_brew = 0
    with db.engine.begin() as connection:

        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        first_row = result.first()

        ml_in_barrels = first_row.num_red_ml
        num_potions_to_brew = (ml_in_barrels // 100)

    return [
            {
                "potion_type": [100, 0, 0, 0],
                "quantity": num_potions_to_brew,
            }
        ]
