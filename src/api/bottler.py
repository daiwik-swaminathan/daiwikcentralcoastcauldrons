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

    with db.engine.begin() as connection:

        mapper = {}

        if potions_delivered[0].potion_type[0] > 0:
            mapper['num_red_ml'] = potions_delivered[0].potion_type[0]

        if potions_delivered[0].potion_type[1] > 0:
            mapper['num_green_ml'] = potions_delivered[0].potion_type[1]

        if potions_delivered[0].potion_type[2] > 0:
            mapper['num_blue_ml'] = potions_delivered[0].potion_type[2]

        global_inventory_result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        global_first_row = global_inventory_result.first()
        
        red_ml = global_first_row.num_red_ml
        green_ml = global_first_row.num_green_ml
        blue_ml = global_first_row.num_blue_ml

        # print('red ml in stock for potion', potion_type, ':', red_ml)
        # print('green ml in stock for potion', potion_type, ':', green_ml)
        # print('blue ml in stock for potion', potion_type, ':', blue_ml)

        # take a dictionary containing the ml requirements of the specific potion type
        # ex: 50 50 0 0
        # then filter out the zeros

        mixed_or_full = max(potions_delivered[0].potion_type)
        requirement_nums = list(mapper.values())
        ml_types = list(mapper.keys())

        if(mixed_or_full == 100):
            # Update the ml
            connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET {ml_types[0]} = {ml_types[0]} - :ml_consumed"),
                [{'ml_consumed':(potions_delivered[0].quantity*mixed_or_full)}])

        elif(mixed_or_full == 50):
            # Update the ml
            connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET {ml_types[0]} = {ml_types[0]} - :ml_consumed, {ml_types[1]} = {ml_types[1]} - :ml_consumed"),
                [{'ml_consumed': potions_delivered[0].quantity * mixed_or_full}])

            # connection.execute(sqlalchemy.text("UPDATE global_inventory SET :ml_type1 = :ml_type1 - :ml_consumed, :ml_type2 = :ml_type2 - :ml_consumed"),
            #     [{'ml_type1':ml_types[0], 'ml_type2':ml_types[1], 'ml_consumed':(potions_delivered[0].quantity*mixed_or_full)}])

        # Update the inventory for this potion type
        connection.execute(sqlalchemy.text(f"UPDATE catalogs SET inventory = inventory + :num_potions WHERE red = :red AND green = :green AND blue = :blue AND dark = :dark"),
            [{'num_potions':potions_delivered[0].quantity,
              'red':potions_delivered[0].potion_type[0],
              'green':potions_delivered[0].potion_type[1],
              'blue':potions_delivered[0].potion_type[2],
              'dark':potions_delivered[0].potion_type[3]}])

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

        # For assignment 3, I am giving priority to mixed potions to be brewed first
        potion_result = connection.execute(sqlalchemy.text("SELECT * FROM catalogs ORDER BY inventory, CASE WHEN red != 100 AND green != 100 AND blue != 100 AND dark != 100 THEN 0 ELSE 1 END;"))
        first_row = potion_result.first()
        potion_type = [first_row.red, first_row.green, first_row.blue, first_row.dark]

        global_inventory_result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        global_first_row = global_inventory_result.first()
        red_ml = global_first_row.num_red_ml
        green_ml = global_first_row.num_green_ml
        blue_ml = global_first_row.num_blue_ml

        mapper = {}

        if first_row.red > 0:
            mapper['num_red_ml'] = (first_row.red, red_ml)

        if first_row.green > 0:
            mapper['num_green_ml'] = (first_row.green, green_ml)

        if first_row.blue > 0:
            mapper['num_blue_ml'] = (first_row.blue, blue_ml)

        print('red ml in stock for potion', potion_type, ':', red_ml)
        print('green ml in stock for potion', potion_type, ':', green_ml)
        print('blue ml in stock for potion', potion_type, ':', blue_ml)

        # take a dictionary containing the ml requirements of the specific potion type
        # ex: 50 50 0 0
        # then filter out the zeros

        mixed_or_full = max(potion_type)
        requirement_nums = list(mapper.values())
        ml_types = list(mapper.keys())

        if(mixed_or_full == 100):
            # Brew up to 5 potions of a single color
            num_potions_to_brew = min(requirement_nums[0][1] // 100, 5)
            # connection.execute(sqlalchemy.text("UPDATE global_inventory SET :ml_type = :ml_type - :ml_consumed"),
            #     [{'ml_type':ml_types[0], 'ml_consumed':(num_potions_to_brew*100)}])
        elif(mixed_or_full == 50):
            # Brew up to 5 potions of a mixed color
            # For now, we assume we can only mix 50/50 potions
            num_potions_to_brew = min(min(requirement_nums[0][1] // 50, requirement_nums[1][1] // 50), 5)
            # connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET {ml_type} = {ml_in_barrels}"))

    if num_potions_to_brew == 0:
        return []

    return [
            {
                "potion_type": potion_type,
                "quantity": num_potions_to_brew,
            }
        ]
