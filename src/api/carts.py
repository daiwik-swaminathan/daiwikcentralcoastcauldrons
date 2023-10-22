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
        connection.execute(sqlalchemy.text("INSERT INTO cart_items (cart_id, quantity, catalog_id) SELECT :cart_id, :quantity, catalogs.catalog_id FROM catalogs WHERE catalogs.name = :item_sku"),
        [{"cart_id": cart_id, "quantity": quantity, "item_sku": item_sku}])

    return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """

    print('In checkout...')

    print('cart checkout is:', cart_checkout.payment)

    # revenue = (potion_price * num_potions)

    # Update the table
    with db.engine.begin() as connection:

        price_result = connection.execute(sqlalchemy.text("SELECT price FROM cart_items JOIN catalogs ON catalogs.catalog_id = cart_items.catalog_id WHERE cart_id = :cart_id LIMIT 1;"), [{'cart_id':cart_id}])
        potion_price = price_result.scalar()

        customer_name = connection.execute(sqlalchemy.text("SELECT customer_name FROM carts WHERE cart_id = :cart_id;"), [{'cart_id':cart_id}]).scalar()

        # Create checkout transaction
        checkout_transaction_id = connection.execute(sqlalchemy.text(f"INSERT INTO inventory_transactions (description) VALUES ('{customer_name} completed their checkout') RETURNING inventory_transaction_id;")).scalar()
        
        # Note down update to potion inventories
        num_potions = 0
        result = connection.execute(sqlalchemy.text("SELECT * FROM cart_items JOIN catalogs on cart_items.catalog_id = catalogs.catalog_id JOIN shop_stats ON catalogs.name = shop_stats.name"))
        for row in result:
            print('hi there')
            num_potions += row.quantity
            shop_stat_id = connection.execute(sqlalchemy.text("SELECT shop_stat_id FROM shop_stats WHERE name = :potion_name"), [{'potion_name':row.name}]).scalar()
            connection.execute(sqlalchemy.text(f"INSERT INTO inventory_ledger_entries (inventory_transaction_id, shop_stat_id, change) SELECT :checkout_transaction_id, :shop_stat_id, :change;"),
                [{'checkout_transaction_id':checkout_transaction_id, 'shop_stat_id':shop_stat_id, 'change':(-1*row.quantity)}])

        # Noting down update to gold
        shop_stat_id = connection.execute(sqlalchemy.text("SELECT shop_stat_id FROM shop_stats WHERE name = 'gold'")).scalar()
        connection.execute(sqlalchemy.text("INSERT INTO inventory_ledger_entries (inventory_transaction_id, shop_stat_id, change) SELECT :checkout_transaction_id, :shop_stat_id, :revenue;"),
            [{'checkout_transaction_id':checkout_transaction_id, 'shop_stat_id':shop_stat_id, 'revenue':num_potions*potion_price}])

        # Delete the cart (the cart items will also be deleted as a consequence)
        connection.execute(sqlalchemy.text("DELETE FROM carts WHERE cart_id = :cart_id"), [{'cart_id':cart_id}])


    return {"total_potions_bought": num_potions, "total_gold_paid": potion_price*num_potions}
