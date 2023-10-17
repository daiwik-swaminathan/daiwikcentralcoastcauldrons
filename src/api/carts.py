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

    customer_name = new_cart.customer

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("INSERT INTO carts (customer_name) VALUES (:customer_name) RETURNING cart_id"), [{"customer_name": customer_name}])
        new_cart_id = result.scalar()

    print('new cart id is:', new_cart_id)

    return {"cart_id": new_cart_id}


@router.get("/{cart_id}")
def get_cart(cart_id: int):
    """ """

    return {}


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """

    quantity = cart_item.quantity

    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text("INSERT INTO cart_items (cart_id, quantity, catalog_id) SELECT :cart_id, :quantity, catalogs.catalog_id FROM catalogs WHERE catalogs.sku = :item_sku"),
        [{"cart_id": cart_id, "quantity": quantity, "item_sku": item_sku}])

    return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """

    print('In checkout...')

    print('cart checkout is:', cart_checkout.payment)

    num_potions = 0
    gold = 0
    potion_type = ''
    with db.engine.begin() as connection:

        # Gets the sum of the number of potions in the cart
        num_potions_result = connection.execute(sqlalchemy.text("SELECT SUM(quantity) FROM cart_items JOIN catalogs ON cart_items.catalog_id = catalogs.catalog_id WHERE catalogs.inventory > 0 AND cart_items.cart_id = :cart_id;"),
                                         [{'cart_id':cart_id}])
        num_potions = num_potions_result.scalar()

        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        first_row = result.first()

        gold = first_row.gold

        price_result = connection.execute(sqlalchemy.text("SELECT price FROM cart_items JOIN catalogs ON catalogs.catalog_id = cart_items.catalog_id WHERE cart_id = :cart_id LIMIT 1;"), [{'cart_id':cart_id}])
        potion_price = price_result.scalar()

    print('Buying', num_potions, 'potions...')

    # For now, we sell all the potions in inventory
    gold += (potion_price * num_potions)

    # Update the table
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = :gold"), [{'gold':gold}])
        connection.execute(sqlalchemy.text("UPDATE catalogs SET inventory = catalogs.inventory - cart_items.quantity FROM cart_items WHERE catalogs.catalog_id = cart_items.catalog_id and cart_items.cart_id = :cart_id;"),
                            [{'cart_id':cart_id}])

        # Delete the cart (the cart items will also be deleted as a consequence)
        connection.execute(sqlalchemy.text("DELETE FROM carts WHERE cart_id = :cart_id"), [{'cart_id':cart_id}])


    return {"total_potions_bought": num_potions, "total_gold_paid": potion_price*num_potions}
