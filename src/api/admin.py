from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.post("/reset")
def reset():
    """
    Reset the game state. Gold goes to 100, all potions are removed from
    inventory, and all barrels are removed from inventory. Carts are all reset.
    """

    print('Resetting shop...')

    # Update the table
    with db.engine.begin() as connection:
        # connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_red_potions = 0"))
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_red_ml = 0"))
        # connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_green_potions = 0"))
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_green_ml = 0"))
        # connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_blue_potions = 0"))
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_blue_ml = 0"))
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = 100"))
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET barrel_to_buy = 0"))

        # Reset carts
        connection.execute(sqlalchemy.text("TRUNCATE carts"))
        connection.execute(sqlalchemy.text("TRUNCATE cart_items"))

        # Empty potion inventory
        connection.execute(sqlalchemy.text("UPDATE catalogs SELECT inventory = 0"))

        print('Updated the database table')

    return "OK"


@router.get("/shop_info/")
def get_shop_info():
    """ """

    # TODO: Change me!
    return {
        "shop_name": "Potion Shop",
        "shop_owner": "Potion Seller",
    }

