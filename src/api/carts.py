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
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_red_potions FROM global_inventory"))
        num_potions_row = result.fetchone()
        num_potions = num_potions_row[0]

        result = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory"))
        gold_row = result.fetchone()
        gold = num_potions_row[0]

        # debug
        print('Entered carts new block. num_red_potions is', num_red_potions)
        print('Entered carts new block. gold is', gold)

    # Check if the number of red potions in inventory is 10+
    # In this case, don't go through with the sale
    if num_potions >= 10:
        print('Carts checkout. We have more than 10 red potions.')
        return {"total_potions_bought": 0, "total_gold_paid": 0}

    # We have less than 10 red potions
    # Subtract number of potions, increase gold amount
    num_potions -= 1
    gold += 50

    # Update the table
    with engine.begin() as connection:
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_potions = {num_potions}"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold = {gold}"))
        print('Updated the database table')

    return {"total_potions_bought": 1, "total_gold_paid": 50}
