from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import math
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/audit",
    tags=["audit"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.get("/inventory")
def get_inventory():
    """ """

    print('In get inventory')
    
    num_potions = 0
    ml_in_barrels = 0
    gold = 0
    with db.engine.begin() as connection:

        gold = connection.execute(sqlalchemy.text("SELECT SUM(change) FROM inventory_ledger_entries JOIN shop_stats ON inventory_ledger_entries.shop_stat_id = shop_stats.shop_stat_id WHERE shop_stats.name = 'gold' ")).scalar()

        ml_in_barrels = connection.execute(sqlalchemy.text("SELECT SUM(change) AS total_potion_change FROM shop_stats JOIN inventory_ledger_entries ON shop_stats.shop_stat_id = inventory_ledger_entries.shop_stat_id WHERE shop_stats.name LIKE '%ml%';")).scalar()

        num_potions = connection.execute(sqlalchemy.text("SELECT SUM(change) AS total_potion_change FROM shop_stats JOIN inventory_ledger_entries ON shop_stats.shop_stat_id = inventory_ledger_entries.shop_stat_id WHERE shop_stats.name LIKE '%POTION%';")).scalar()

    print('ml_in_barrels is', ml_in_barrels)
    print('num_potions is', num_potions)
    print('gold is', gold)

    return {"number_of_potions": num_potions, "ml_in_barrels": ml_in_barrels, "gold": gold}

class Result(BaseModel):
    gold_match: bool
    barrels_match: bool
    potions_match: bool

# Gets called once a day
@router.post("/results")
def post_audit_results(audit_explanation: Result):
    """ """
    print(audit_explanation)

    return "OK"
