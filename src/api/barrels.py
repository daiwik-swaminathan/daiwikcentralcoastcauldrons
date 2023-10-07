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
    ml_type = ''
    with db.engine.begin() as connection:

        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        first_row = result.first()

        last_barrel_type = first_row.last_barrel_type

        if last_barrel_type == 0:
            ml_in_barrels = first_row.num_red_ml
            ml_type = 'num_red_ml'
        elif last_barrel_type == 1:
            ml_in_barrels = first_row.num_green_ml
            ml_type = 'num_green_ml'
        else:
            ml_in_barrels = first_row.num_blue_ml
            ml_type = 'num_blue_ml'

        gold = first_row.gold

        # We will, for now, always be buying only one barrel
        gold -= barrels_delivered[0].price
        ml_in_barrels += barrels_delivered[0].ml_per_barrel

        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET {ml_type} = {ml_in_barrels}"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold = {gold}"))

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)

    # Parse through the barrel merchant's catalog

    # My logic is that the shop will only buy one barrel at a time
    # It will switch out which barrel it buys.
    # Ex: It will first look to buy a green barrel, blue barrel, red barrel, and then back to green.

    # Get which kind of barrel was purchased last
    last_barrel_type = 0
    with db.engine.begin() as connection:

        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        first_row = result.first()

        last_barrel_type = first_row.last_barrel_type

    # Go through the merchant's catalog and figure out which barrel we should buy this time
    for barrel in wholesale_catalog:

        # If the red barrel is available AND the last barrel purchased was a blue barrel
        if barrel.potion_type[0] == 0 and last_barrel_type == 2:
            last_barrel_type = 0
            with db.engine.begin() as connection:
                connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET last_barrel_type = {last_barrel_type}"))
            return [
                {
                    "sku": "SMALL_RED_BARREL",
                    "quantity": 1,
                }
            ] 
        
        # If the green barrel is available AND the last barrel purchased was a red barrel
        if barrel.potion_type[0] == 1 and last_barrel_type == 0:
            last_barrel_type = 1
            with db.engine.begin() as connection:
                connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET last_barrel_type = {last_barrel_type}"))
            return [
                {
                    "sku": "SMALL_GREEN_BARREL",
                    "quantity": 1,
                }
            ]

        # If the blue barrel is available AND the last barrel purchased was a green barrel
        if barrel.potion_type[0] == 2 and last_barrel_type == 1:
            last_barrel_type = 2
            with db.engine.begin() as connection:
                connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET last_barrel_type = {last_barrel_type}"))
            return [
                {
                    "sku": "SMALL_BLUE_BARREL",
                    "quantity": 1,
                }
            ]

    # By default, buy a red barrel
    last_barrel_type = 0
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET last_barrel_type = {last_barrel_type}"))
    return [
        {
            "sku": "SMALL_RED_BARREL",
            "quantity": 1,
        }
    ]
