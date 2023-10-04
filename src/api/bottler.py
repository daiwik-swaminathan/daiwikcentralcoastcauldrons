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

    # Decrease red ml by 100, increase red potions by 10

    ml_in_barrels = 0
    num_red_potions = 0
    with db.engine.begin() as connection:

        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        first_row = result.first()
        print(f"red ml {first_row.num_red_ml}")
        print(f"num_red_potions {first_row.num_red_potions}")

        ml_in_barrels = first_row.num_red_ml
        num_red_potions = first_row.num_red_potions

        num_potions_to_brew = (ml_in_barrels // 100)
        num_red_potions += num_potions_to_brew
        ml_in_barrels -= 100 * num_potions_to_brew

        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_ml = {ml_in_barrels}"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold = {gold}"))
        print('Updated the database table')

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
    num_red_potions = 0
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        first_row = result.first()
        print(f"red potions {first_row.num_red_potions}")

        num_red_potions = first_row.num_red_potions

    return [
            {
                "potion_type": [100, 0, 0, 0],
                "quantity": num_red_potions,
            }
        ]
