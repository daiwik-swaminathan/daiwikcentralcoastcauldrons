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

        # Reset everything transaction and ledger related
        connection.execute(sqlalchemy.text("TRUNCATE inventory_transactions CASCADE"))

        result = connection.execute(sqlalchemy.text("INSERT INTO inventory_transactions (description) VALUES ('Shop burnt down...everything back to zero, gold set to 100') RETURNING inventory_transaction_id;"))
        reset_transaction_id = result.scalar()
        
        connection.execute(sqlalchemy.text("INSERT INTO inventory_ledger_entries (inventory_transaction_id, shop_stat_id, change) SELECT :reset_transaction_id, shop_stat_id, CASE WHEN name = 'gold' THEN 100 ELSE 0 END FROM shop_stats;"), [{'reset_transaction_id':reset_transaction_id}])

        # Reset carts
        connection.execute(sqlalchemy.text("TRUNCATE carts CASCADE"))

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

