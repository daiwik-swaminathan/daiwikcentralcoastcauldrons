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

        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        first_row = result.first()

        gold = first_row.gold

        num_potions = first_row.num_red_potions
        num_potions += first_row.num_green_potions
        num_potions += first_row.num_blue_potions

        ml_in_barrels = first_row.num_red_ml
        ml_in_barrels += first_row.num_green_ml
        ml_in_barrels += first_row.num_blue_ml

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
