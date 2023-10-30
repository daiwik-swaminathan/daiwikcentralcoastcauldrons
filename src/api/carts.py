from fastapi import APIRouter, Depends, Request, HTTPException
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from sqlalchemy import func, MetaData
from src import database as db

temp_cart_table = {}
cart_counter = 0
from enum import Enum

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)

class search_sort_options(str, Enum):
    customer_name = "customer_name"
    item_sku = "item_sku"
    line_item_total = "line_item_total"
    timestamp = "timestamp"

class search_sort_order(str, Enum):
    asc = "asc"
    desc = "desc"   

@router.get("/search/", tags=["search"])
def search_orders(
    customer_name: str = "",
    potion_sku: str = "",
    search_page: str = "",
    sort_col: search_sort_options = search_sort_options.timestamp,
    sort_order: search_sort_order = search_sort_order.desc,
):
    """
    Search for cart line items by customer name and/or potion sku.

    Customer name and potion sku filter to orders that contain the 
    string (case insensitive). If the filters aren't provided, no
    filtering occurs on the respective search term.

    Search page is a cursor for pagination. The response to this
    search endpoint will return previous or next if there is a
    previous or next page of results available. The token passed
    in that search response can be passed in the next search request
    as search page to get that page of results.

    Sort col is which column to sort by and sort order is the direction
    of the search. They default to searching by timestamp of the order
    in descending order.

    The response itself contains a previous and next page token (if
    such pages exist) and the results as an array of line items. Each
    line item contains the line item id (must be unique), item sku, 
    customer name, line item total (in gold), and timestamp of the order.
    Your results must be paginated, the max results you can return at any
    time is 5 total line items.

    customer_name = "customer_name"
    item_sku = "item_sku"
    line_item_total = "line_item_total"
    timestamp = "timestamp"
    """

    with db.engine.connect() as conn:

        if search_page != '':
            offset = int(search_page)
        else:
            offset = 0

        order_by = None

        metadata = MetaData()
        metadata.reflect(bind=db.engine)

        if sort_col is search_sort_options.customer_name:
            order_by = metadata.tables['carts'].c.customer_name
        elif sort_col is search_sort_options.item_sku:
            order_by = metadata.tables['catalogs'].c.name
        elif sort_col is search_sort_options.line_item_total:
            order_by = metadata.tables['catalogs'].c.price * func.sum(metadata.tables['cart_items'].c.quantity)
        elif sort_col is search_sort_options.timestamp:
            order_by = metadata.tables['cart_items'].c.time_created
        else:
            assert False

        if sort_order is search_sort_order.asc:
            order_by = order_by.asc()
        else:
            order_by = order_by.desc()

        stmt = (
            sqlalchemy.select(
                func.upper(metadata.tables['carts'].c.customer_name).label('customer'),
                metadata.tables['catalogs'].c.name.label('item'),
                (metadata.tables['catalogs'].c.price * func.sum(metadata.tables['cart_items'].c.quantity)).label('gold'),
                metadata.tables['cart_items'].c.time_created.label('time'),
                metadata.tables['cart_items'].c.quantity
            )
            .select_from(
                metadata.tables['carts'].join(metadata.tables['cart_items'], metadata.tables['carts'].c.cart_id == metadata.tables['cart_items'].c.cart_id)
                .join(metadata.tables['catalogs'], metadata.tables['cart_items'].c.catalog_id == metadata.tables['catalogs'].c.catalog_id))
            .group_by(metadata.tables['carts'].c.customer_name,
                      metadata.tables['catalogs'].c.name,
                      metadata.tables['catalogs'].c.price,
                      metadata.tables['cart_items'].c.time_created,
                      metadata.tables['cart_items'].c.quantity)
            .limit(5)
            .offset(offset * 5)
            .order_by(order_by)
        )

        # filter only if name parameter is passed
        if customer_name != "":
            customer_name = customer_name.upper()
            stmt = stmt.where(metadata.tables['carts'].c.customer_name.ilike(f"%{customer_name}%"))

        # filter only if potion_sku parameter is passed
        if potion_sku != "":
            potion_sku = potion_sku.upper()
            stmt = stmt.where(metadata.tables['catalogs'].c.name.ilike(f"%{potion_sku}%"))

        result = conn.execute(stmt)
        json = []

        i = 0
        for row in result:
            item_desc = ''
            item_desc += str(row.quantity)
            item_desc += ' '
            item_desc += row.item
            json.append(
            {
                "line_item_id": i,
                "item_sku": item_desc,
                "customer_name": row.customer,
                "line_item_total": row.gold,
                "timestamp": row.time,
            })
            i += 1


    # return json

    previous_page = ''
    next_page = ''

    if offset > 0:
        previous_page = str(offset - 1)

    next_page = str(offset + 1)

    return {
        "previous": previous_page,
        "next": next_page,
        "results": json
    }


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

            # Add check to ensure there are still available potions to buy
            num_potions_available = connection.execute(sqlalchemy.text("SELECT SUM(change) FROM inventory_ledger_entries WHERE shop_stat_id = :shop_stat_id",
                                                                       ), [{'shop_stat_id':shop_stat_id}]).scalar()
            
            if num_potions_available < row.quantity:
                # Throw HTTP error here

                # Delete the cart first (the cart items will also be deleted as a consequence)
                # connection.execute(sqlalchemy.text("DELETE FROM carts WHERE cart_id = :cart_id"), [{'cart_id':cart_id}])

                error_message = "Not enough potions available to buy."
                raise HTTPException(status_code=400, detail=error_message)

            connection.execute(sqlalchemy.text(f"INSERT INTO inventory_ledger_entries (inventory_transaction_id, shop_stat_id, change) SELECT :checkout_transaction_id, :shop_stat_id, :change;"),
                [{'checkout_transaction_id':checkout_transaction_id, 'shop_stat_id':shop_stat_id, 'change':(-1*row.quantity)}])

        # Noting down update to gold
        shop_stat_id = connection.execute(sqlalchemy.text("SELECT shop_stat_id FROM shop_stats WHERE name = 'gold'")).scalar()
        connection.execute(sqlalchemy.text("INSERT INTO inventory_ledger_entries (inventory_transaction_id, shop_stat_id, change) SELECT :checkout_transaction_id, :shop_stat_id, :revenue;"),
            [{'checkout_transaction_id':checkout_transaction_id, 'shop_stat_id':shop_stat_id, 'revenue':num_potions*potion_price}])

        # Delete the cart (the cart items will also be deleted as a consequence)
        # connection.execute(sqlalchemy.text("DELETE FROM carts WHERE cart_id = :cart_id"), [{'cart_id':cart_id}])


    return {"total_potions_bought": num_potions, "total_gold_paid": potion_price*num_potions}
