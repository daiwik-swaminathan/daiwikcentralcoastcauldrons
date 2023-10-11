from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

temp_cart_table = {}
cart_counter = 0

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
    global cart_counter
    temp_id = cart_counter
    cart_counter += 1

    print('temp id is:', temp_id, 'cart_counter is', cart_counter)
    # need to do this
    return {"cart_id": temp_id}


@router.get("/{cart_id}")
def get_cart(cart_id: int):
    """ """

    return {}


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """

    # Track what potion and how many
    temp_cart_table[cart_id] = (item_sku, cart_item.quantity)

    return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """

    print('In checkout...')

    print('cart checkout is:', cart_checkout.payment)

    (item_sku, total_potions_bought) = temp_cart_table[cart_id]

    num_potions = 0
    gold = 0
    potion_type = ''
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        first_row = result.first()

        if item_sku == "RED_POTION_0":
            print('Buying red potions...')
            num_potions = first_row.num_red_potions
            potion_type = 'num_red_potions'
        elif item_sku == "GREEN_POTION_0":
            print('Buying green potions...')
            num_potions = first_row.num_green_potions
            potion_type = 'num_green_potions'
        else:
            print('Buying blue potions...')
            num_potions = first_row.num_blue_potions
            potion_type = 'num_blue_potions'

        gold = first_row.gold

    if total_potions_bought > num_potions:
        return {"total_potions_bought": 0, "total_gold_paid": 0}

    print('Buying', total_potions_bought, 'potions...')

    # For now, we sell all the potions in inventory
    gold += (50 * total_potions_bought)
    num_potions -= total_potions_bought

    # Update the table
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET {potion_type} = {num_potions}"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold = {gold}"))
        # if total_potions_bought > 0:
        #     connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET barrel_to_buy = {(barrel_to_buy + 1) % 3}"))

    return {"total_potions_bought": total_potions_bought, "total_gold_paid": 50*total_potions_bought}
