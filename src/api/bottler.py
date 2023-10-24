from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)

index_to_ml = {0:'red_ml', 1:'green_ml', 2:'blue_ml', 3:'dark_ml'}

barrel_to_bottle = {'SMALL_RED_BARREL':'RED_POTION_0', 'SMALL_GREEN_BARREL':'GREEN_POTION_0', 'SMALL_BLUE_BARREL':'BLUE_POTION_0'}

class PotionInventory(BaseModel):
    potion_type: list[int]
    quantity: int

@router.post("/deliver")
def post_deliver_bottles(potions_delivered: list[PotionInventory]):
    """ ml down, bottles up """
    print(potions_delivered)

    if potions_delivered == []:
        return "OK"

    if potions_delivered[0].quantity == 0:
        return "OK"

    with db.engine.begin() as connection:

        potion_name = inventory_transaction_id = connection.execute(sqlalchemy.text("SELECT name FROM catalogs WHERE red_ml = :red_value AND green_ml = :green_value AND blue_ml = :blue_value AND dark_ml = :dark_value;"),
            [{'red_value':potions_delivered[0].potion_type[0], 'green_value':potions_delivered[0].potion_type[1], 'blue_value':potions_delivered[0].potion_type[2], 'dark_value':potions_delivered[0].potion_type[3]}]).scalar()

        inventory_transaction_id = connection.execute(sqlalchemy.text(f"INSERT INTO inventory_transactions (description) VALUES ('Converting ml to make {potions_delivered[0].quantity} {potion_name} potions') RETURNING inventory_transaction_id;")).scalar()

        for i in range(len(potions_delivered[0].potion_type)):

            if potions_delivered[0].potion_type[i] > 0:

                # potion_quantity_result = connection.execute(sqlalchemy.text(f"SELECT SUM(change) FROM shop_stats JOIN inventory_transactions ON shop_stats.shop_stat_id = inventory_ledger_entries.shop_stat_id WHERE shop_stats.name = {index_to_ml[i]}"))

                # inventory_transaction_id = connection.execute(sqlalchemy.text(f"INSERT INTO inventory_transactions (description) VALUES ('Reducing {index_to_ml[i]} by {potions_delivered[0].potion_type[i]}') RETURNING inventory_transaction_id;")).scalar()

                shop_stat_id = connection.execute(sqlalchemy.text("SELECT shop_stat_id FROM shop_stats WHERE shop_stats.name = :value"),
                    [{'value':index_to_ml[i]}]).scalar()
                
                connection.execute(sqlalchemy.text("INSERT INTO inventory_ledger_entries (inventory_transaction_id, shop_stat_id, change) VALUES (:inventory_transaction_id, :shop_stat_id, :change);"),
                    [{'inventory_transaction_id':inventory_transaction_id, 'shop_stat_id':shop_stat_id, 'change':(potions_delivered[0].quantity * -1 * potions_delivered[0].potion_type[i])}])

        # sku = connection.execute(sqlalchemy.text("SELECT name FROM catalogs WHERE red_ml = :red AND green_ml = :green AND blue_ml = :blue AND dark_ml = :dark"),
        #             [{'red':potions_delivered[0].potion_type[0], 'green':potions_delivered[0].potion_type[1], 'blue':potions_delivered[0].potion_type[2], 'dark':potions_delivered[0].potion_type[3]}]).scalar()

        # inventory_transaction_id = connection.execute(sqlalchemy.text(f"INSERT INTO inventory_transactions (description) VALUES ('Brewed {potions_delivered[0].quantity} {sku}') RETURNING inventory_transaction_id;")).scalar()

        shop_stat_id = connection.execute(sqlalchemy.text("SELECT shop_stat_id FROM shop_stats WHERE name = :potion_name"), [{'potion_name':potion_name}])

        connection.execute(sqlalchemy.text("INSERT INTO inventory_ledger_entries (inventory_transaction_id, shop_stat_id, change) SELECT :inventory_transaction_id, shop_stat_id, :change FROM shop_stats WHERE name = :potion_name;"),
                    [{'inventory_transaction_id':inventory_transaction_id, 'potion_name':potion_name, 'change':potions_delivered[0].quantity}])

    return "OK"

# Gets called 4 times a day
@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """

    print('Planning to convert ml to bottles...')

    potion_plan = []
    with db.engine.begin() as connection:

        # result = connection.execute(sqlalchemy.text("SELECT shop_stats.name, SUM(change) as amount FROM shop_stats JOIN inventory_ledger_entries ON shop_stats.shop_stat_id = inventory_ledger_entries.shop_stat_id WHERE shop_stats.name LIKE '%POTION%' GROUP BY name ORDER BY amount LIMIT 1;"))
        # chosen_row = result.first()
        # potion_sku = chosen_row.name

        # potion_type_result = connection.execute(sqlalchemy.text("SELECT red_ml, green_ml, blue_ml, dark_ml FROM catalogs WHERE sku = :potion_sku;"), [{'potion_sku':potion_sku}])
        # catalog_row = potion_type_result.first()

        # potion_type = [catalog_row.red_ml, catalog_row.green_ml, catalog_row.blue_ml, catalog_row.dark_ml]

        # potion_ml_amount = max(potion_type)

        # Figure out later how to get number of potions, for now just hard code 5
        # potion_quantity_result = connection.execute(sqlalchemy.text("SELECT SUM(change) FROM shop_stats JOIN inventory_transactions ON shop_stats.shop_stat_id = inventory_ledger_entries.shop_stat_id WHERE shop_stats.name = 'green_ml' "))

        last_barrel_purchased = connection.execute(sqlalchemy.text("SELECT SPLIT_PART(SPLIT_PART(description, ' ', 2), ' ', 1) AS last_barrel_purchased FROM inventory_transactions WHERE description LIKE '%BARREL%' ORDER BY created_at DESC LIMIT 1;")).scalar()
        
        if last_barrel_purchased is None:
            return potion_plan

        potion_to_brew = barrel_to_bottle[last_barrel_purchased]

        potion_type_result = connection.execute(sqlalchemy.text("SELECT red_ml, green_ml, blue_ml, dark_ml FROM catalogs WHERE name = :potion_sku;"), [{'potion_sku':potion_to_brew}])
        catalog_row = potion_type_result.first()

        potion_type = [catalog_row.red_ml, catalog_row.green_ml, catalog_row.blue_ml, catalog_row.dark_ml]

        # You would need to loop through potion type to see if you have enough ml to brew the 5 potions

        potion_plan.append({
            "potion_type": potion_type,
            "quantity": 5
        })

    return potion_plan
