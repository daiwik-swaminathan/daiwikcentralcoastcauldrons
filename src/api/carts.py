from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)


class NewCart(BaseModel):
    customer: str


@router.post("/")
def create_cart(new_cart: NewCart):
    """ """
    return {"cart_id": 1}


@router.get("/{cart_id}")
def get_cart(cart_id: int):
    """ """

    return {}


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """

    return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """

    # Get the amount of red potions and gold from the database
    num_potions = 0
    gold = 0
    potion_type = ''
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        first_row = result.first()

        last_barrel_type = first_row.last_barrel_type

        if last_barrel_type == 0:
            num_potions = first_row.num_red_potions
            potion_type = 'num_red_potions'
        elif last_barrel_type == 1:
            num_potions = first_row.num_green_potions
            potion_type = 'num_green_potions'
        else:
            num_potions = first_row.num_blue_potions
            potion_type = 'num_blue_potions'

        gold = first_row.gold

    # Check if the number of potions in inventory is 10+
    # In this case, don't go through with the sale
    # if num_potions >= 10:
    #     print('Carts checkout. We have more than 10 potions for', potion_type)
    #     return {"total_potions_bought": 0, "total_gold_paid": 0}

    # We have less than 10 red potions
    # For now, only one potion can be bought at a time
    num_potions -= 1
    gold += 50

    # Update the table
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET {potion_type} = {num_potions}"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold = {gold}"))

    return {"total_potions_bought": 1, "total_gold_paid": 50}
