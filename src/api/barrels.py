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

    if(len(barrels_delivered) == 0):
        return "OK"

    print('Barrel has been delivered!')

    print(barrels_delivered)

    # ml_in_barrels = 0
    red_ml = 0
    green_ml = 0
    blue_ml = 0
    gold = 0
    ml_type = ''
    with db.engine.begin() as connection:

        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        first_row = result.first()

        gold = first_row.gold

        # if barrels_delivered[0].sku == 'SMALL_RED_BARREL':
        #     print('Received small red barrel')
        #     red_ml = first_row.num_red_ml
        #     ml_type = 'num_red_ml'
        # elif barrels_delivered[0].sku == 'SMALL_GREEN_BARREL':
        #     print('Received small green barrel')
        #     green_ml = first_row.num_green_ml
        #     ml_type = 'num_green_ml'
        # else:
        #     print('Received small blue barrel')
        #     blue_ml = first_row.num_blue_ml
        #     ml_type = 'num_blue_ml'

        cost = 0

        for barrel in barrels_delivered:
            if barrel.sku == 'SMALL_RED_BARREL':
                print('Received small red barrel')
                red_ml = first_row.num_red_ml + barrel.ml_per_barrel
                print('red ml will now be:', red_ml)
            elif barrel.sku == 'SMALL_GREEN_BARREL':
                print('Received small green barrel')
                green_ml = first_row.num_green_ml + barrel.ml_per_barrel
                print('green ml will now be:', green_ml)
            else:
                print('Received small blue barrel')
                blue_ml = first_row.num_blue_ml + barrel.ml_per_barrel
                print('blue ml will now be:', blue_ml)
            cost += barrel.price

        # Buying a small red, green, and blue barrel
        print('Converting to ml...')
        gold -= cost

        print('Barrel deliver endpoint')
        print('gold is:', gold)

        # connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET {ml_type} = {ml_in_barrels}"))
        # connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold = {gold}"))

        connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = :gold"), [{'gold':gold}])
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_red_ml = :red_ml"), [{'red_ml':red_ml}])
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_green_ml = :green_ml"), [{'green_ml':green_ml}])
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_blue_ml = :blue_ml"), [{'blue_ml':blue_ml}])

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """

    print('Taking a look at barrel catalog...')

    print(wholesale_catalog)

    # Parse through the barrel merchant's catalog

    # My logic is that the shop will only buy one barrel at a time
    # It will switch out which barrel it buys.
    # Ex: It will first look to buy a green barrel, blue barrel, red barrel, and then back to green.

    # Get which kind of barrel was purchased last
    # barrel_to_buy = 0
    # with db.engine.begin() as connection:

    #     result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
    #     first_row = result.first()

    #     barrel_to_buy = first_row.barrel_to_buy

    #     print('Last barrel type is:', barrel_to_buy)

    # # Go through the merchant's catalog and figure out which barrel we should buy this time
    # for barrel in wholesale_catalog:

    #     # If the red barrel is available AND the last barrel purchased was a blue barrel
    #     if barrel.sku == 'SMALL_RED_BARREL' and barrel_to_buy == 0:
    #         print('Buying a small red barrel')
            
    #         return [
    #             {
    #                 "sku": "SMALL_RED_BARREL",
    #                 "quantity": 1,
    #             }
    #         ] 
        
    #     # If the green barrel is available AND the last barrel purchased was a red barrel
    #     if barrel.sku == 'SMALL_GREEN_BARREL' and barrel_to_buy == 1:
    #         print('Buying a small green barrel')
            
    #         return [
    #             {
    #                 "sku": "SMALL_GREEN_BARREL",
    #                 "quantity": 1,
    #             }
    #         ]

    #     # If the blue barrel is available AND the last barrel purchased was a green barrel
    #     if barrel.sku == 'SMALL_BLUE_BARREL' and barrel_to_buy == 2:
    #         print('Buying a small blue barrel')
            
    #         return [
    #             {
    #                 "sku": "SMALL_BLUE_BARREL",
    #                 "quantity": 1,
    #             }
    #         ]

    # For assignment 3, we will always be buying a small barrel of each color
    return [
        {
            "sku": "SMALL_RED_BARREL",
            "quantity": 1,
        },
        {
            "sku": "SMALL_GREEN_BARREL",
            "quantity": 1,
        },
        {
            "sku": "SMALL_BLUE_BARREL",
            "quantity": 1,
        }
    ]
