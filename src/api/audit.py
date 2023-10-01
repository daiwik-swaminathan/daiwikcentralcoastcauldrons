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
    
    num_red_potions = 0
    ml_in_barrels = 0
    gold = 0
    with db.engine.begin() as connection:

        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        first_row = result.first()
        print(f"red potions {first_row.num_red_potions}")
        print(f"red ml {first_row.num_red_ml}")
        print(f"gold {first_row.gold}")

        num_red_potions = first_row.num_red_potions
        ml_in_barrels = first_row.num_red_ml
        gold = first_row.gold

    return {"number_of_potions": num_red_potions, "ml_in_barrels": ml_in_barrels, "gold": gold}

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
