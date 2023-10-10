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

    if potions_delivered == []:
        return "OK"

    if potions_delivered[0].quantity == 0:
        return "OK"

    ml_in_barrels = 0
    num_potions = 0
    ml_type = ''
    potion_type = ''
    with db.engine.begin() as connection:

        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        first_row = result.first()

        barrel_to_buy = first_row.barrel_to_buy

        if barrel_to_buy == 0:
            ml_in_barrels = first_row.num_red_ml
            num_potions = first_row.num_red_potions
            ml_type = 'num_red_ml'
            potion_type = 'num_red_potions'
        elif barrel_to_buy == 1:
            ml_in_barrels = first_row.num_green_ml
            num_potions = first_row.num_green_potions
            ml_type = 'num_green_ml'
            potion_type = 'num_green_potions'
        else:
            ml_in_barrels = first_row.num_blue_ml
            num_potions = first_row.num_blue_potions
            ml_type = 'num_blue_ml'
            potion_type = 'num_blue_potions'

        print('bottler deliver endpoint (before value update)')
        print('ml_type is', ml_type, 'ml_in_barrels is', ml_in_barrels)
        print('num_potions is', num_potions)

        old_ml = ml_in_barrels

        num_potions += potions_delivered[0].quantity
        ml_in_barrels -= 100 * potions_delivered[0].quantity

        print('bottler deliver endpoint (after value update)')
        print('ml_type is', ml_type, 'ml_in_barrels is', ml_in_barrels)
        print('num_potions is', num_potions)

        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET {ml_type} = {ml_in_barrels}"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET {potion_type} = {num_potions}"))
        if ml_in_barrels < old_ml:
            connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET barrel_to_buy = {(barrel_to_buy + 1) % 3}"))

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

    print('Planning to convert ml to bottles...')

    ml_in_barrels = 0
    num_potions_to_brew = 0
    potion_type = [0, 0, 0, 0]
    with db.engine.begin() as connection:

        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        first_row = result.first()

        barrel_to_buy = first_row.barrel_to_buy

        if barrel_to_buy == 0:
            print('Going to brew red potions...')
            ml_in_barrels = first_row.num_red_ml
            potion_type = [100, 0, 0, 0]
        elif barrel_to_buy == 1:
            print('Going to brew green potions...')
            ml_in_barrels = first_row.num_green_ml
            potion_type = [0, 100, 0, 0]
        else:
            print('Going to brew blue potions...')
            ml_in_barrels = first_row.num_blue_ml
            potion_type = [0, 0, 100, 0]

        print('ml in stock for potion', potion_type, ':', ml_in_barrels)
        num_potions_to_brew = (ml_in_barrels // 100)

    print('potion type:', potion_type, 'quantity:', num_potions_to_brew)

    if num_potions_to_brew == 0:
        return []

    return [
            {
                "potion_type": potion_type,
                "quantity": num_potions_to_brew,
            }
        ]
