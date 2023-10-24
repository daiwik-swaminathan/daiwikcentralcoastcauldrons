from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)

ml_to_barrel = {'red_ml':'SMALL_RED_BARREL', 'green_ml':'SMALL_GREEN_BARREL', 'blue_ml':'SMALL_BLUE_BARREL'}
barrel_to_ml = {'SMALL_RED_BARREL':'red_ml', 'SMALL_GREEN_BARREL':'green_ml', 'SMALL_BLUE_BARREL':'blue_ml'}

class Barrel(BaseModel):
    sku: str

    ml_per_barrel: int
    potion_type: list[int]
    price: int

    quantity: int

@router.post("/deliver")
def post_deliver_barrels(barrels_delivered: list[Barrel]):
    """ """

    if(len(barrels_delivered) == 0):
        return "OK"

    print('Barrel has been delivered!')

    print(barrels_delivered)

    with db.engine.begin() as connection:

        for barrel in barrels_delivered:

            ml_amount = barrel.ml_per_barrel

            ml_id = connection.execute(sqlalchemy.text("SELECT shop_stat_id FROM shop_stats WHERE name = :ml_type;"), [{'ml_type':barrel_to_ml[barrel.sku]}]).scalar()
            gold_id = connection.execute(sqlalchemy.text("SELECT shop_stat_id FROM shop_stats WHERE name = 'gold';")).scalar()

            # barrel_transaction_id = connection.execute(sqlalchemy.text("INSERT INTO inventory_transactions (description) VALUES ('Purchased :barrel for :price gold to make :amount_ml ml') RETURNING inventory_transaction_id;"),
            #     [{'barrel':barrel.sku, 'price':barrel.price, 'amount_ml':ml_amount}]).scalar()

            barrel_transaction_id = connection.execute(sqlalchemy.text(f"INSERT INTO inventory_transactions (description) VALUES ('Purchased {barrel.sku} for {barrel.price} gold to make {ml_amount} ml') RETURNING inventory_transaction_id;")).scalar()

            connection.execute(sqlalchemy.text("INSERT INTO inventory_ledger_entries (inventory_transaction_id, shop_stat_id, change) VALUES (:barrel_transaction_id, :ml_id, :amount_ml), (:barrel_transaction_id, :gold_id, :cost);"),
                [{'barrel_transaction_id':barrel_transaction_id, 'ml_id':ml_id, 'gold_id':gold_id, 'amount_ml':ml_amount, 'cost':(-1*barrel.price)}])

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """

    print('Taking a look at barrel catalog...')

    print(wholesale_catalog)

    barrels = []

    # with db.engine.begin() as connection:

    #     gold = connection.execute(sqlalchemy.text("SELECT SUM(change) FROM inventory_ledger_entries JOIN shop_stats ON inventory_ledger_entries.shop_stat_id = shop_stats.shop_stat_id WHERE shop_stats.name = 'gold' ")).scalar()

    #     result = connection.execute(sqlalchemy.text("SELECT shop_stats.name, SUM(change) as amount FROM shop_stats JOIN inventory_ledger_entries ON shop_stats.shop_stat_id = inventory_ledger_entries.shop_stat_id WHERE shop_stats.name LIKE '%ml%' GROUP BY name ORDER BY amount;"))
    #     chosen_row = result.fetchone()

    #     for barrel in wholesale_catalog:

    #         print('barrel sku is:', barrel.sku, ' and chosen row name is:', chosen_row.name)

    #         print('gold is:', gold, ' and price is:', barrel.price)

    #         if barrel.sku == ml_to_barrel[chosen_row.name] and gold < barrel.price:

    #             print('hello')
    #             chosen_row = result.fetchone()
    #             break

    #     print(chosen_row)

    #     barrels.append( 
    #         {
    #             "sku": ml_to_barrel[chosen_row.name],
    #             "quantity": 1
    #         } ) 

    # barrels.append( 
    #         {
    #             "sku": 'SMALL_RED_BARREL',
    #             "quantity": 1
    #         } ) 

    return barrels
