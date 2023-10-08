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

    print('In checkout...')

    # Get the amount of red potions and gold from the database
    num_potions = 0
    gold = 0
    potion_type = ''
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        first_row = result.first()

        barrel_to_buy = first_row.barrel_to_buy

        if barrel_to_buy == 0:
            print('Buying red potions...')
            num_potions = first_row.num_red_potions
            potion_type = 'num_red_potions'
        elif barrel_to_buy == 1:
            print('Buying green potions...')
            num_potions = first_row.num_green_potions
            potion_type = 'num_green_potions'
        else:
            print('Buying blue potions...')
            num_potions = first_row.num_blue_potions
            potion_type = 'num_blue_potions'

        gold = first_row.gold

    total_potions_bought = num_potions

    print('Buying', total_potions_bought, 'potions...')

    # For now, we sell all the potions in inventory
    gold += (50 * num_potions)
    num_potions = 0

    # Update the table
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET {potion_type} = {num_potions}"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold = {gold}"))
        if total_potions_bought > 0:
            connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET barrel_to_buy = {(barrel_to_buy + 1) % 3}"))

    return {"total_potions_bought": total_potions_bought, "total_gold_paid": (50 * total_potions_bought)}
