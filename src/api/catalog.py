from fastapi import APIRouter
import sqlalchemy
from src import database as db

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """

    catalog = []

    with db.engine.begin() as connection:

        result = connection.execute(sqlalchemy.text("SELECT * FROM catalogs WHERE catalogs.inventory > 0"))

        for row in result:
            catalog.append({
                "sku": row.sku,
                "name": "",
                "quantity": row.inventory,
                "price": row.price,
                "potion_type": [row.red, row.green, row.blue, row.dark],
            })

    # Can return a max of 20 items.

    print('in catalog endpoint!')
    print('catalog is:', catalog)

    return catalog
