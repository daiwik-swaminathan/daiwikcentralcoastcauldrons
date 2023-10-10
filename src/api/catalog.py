from fastapi import APIRouter
import sqlalchemy
from src import database as db

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """

    catalog = []

    num_red_potions = 0
    num_green_potions = 0
    num_blue_potions = 0
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        first_row = result.first()

        num_red_potions = first_row.num_red_potions
        num_green_potions = first_row.num_green_potions
        num_blue_potions = first_row.num_blue_potions

    # Can return a max of 20 items.

    if(num_red_potions > 0):
        catalog.append({
                "sku": "RED_POTION_0",
                "name": "red potion",
                "quantity": num_red_potions,
                "price": 50,
                "potion_type": [100, 0, 0, 0],
        })

    if(num_green_potions > 0):
        catalog.append({
                "sku": "GREEN_POTION_0",
                "name": "green potion",
                "quantity": num_green_potions,
                "price": 1,
                "potion_type": [0, 100, 0, 0],
        })

    if(num_blue_potions > 0):
        catalog.append({
                "sku": "BLUE_POTION_0",
                "name": "blue potion",
                "quantity": num_blue_potions,
                "price": 1,
                "potion_type": [0, 0, 100, 0],
        })

    print('in catalog endpoint!')
    print('catalog is:', catalog)

    return catalog
