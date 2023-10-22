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

        result = connection.execute(sqlalchemy.text("SELECT shop_stats.name, catalogs.name, catalogs.price, catalogs.red_ml, catalogs.green_ml, catalogs.blue_ml, catalogs.dark_ml, SUM(inventory_ledger_entries.change) AS total_change FROM shop_stats JOIN catalogs ON shop_stats.name = catalogs.name LEFT JOIN inventory_ledger_entries ON shop_stats.shop_stat_id = inventory_ledger_entries.shop_stat_id GROUP BY shop_stats.name, catalogs.name, catalogs.price, catalogs.red_ml, catalogs.green_ml, catalogs.blue_ml, catalogs.dark_ml HAVING SUM(inventory_ledger_entries.change) > 0;"))

        for row in result:
            catalog.append({
                "sku": row.name,
                "name": "",
                "quantity": row.total_change,
                "price": row.price,
                "potion_type": [row.red_ml, row.green_ml, row.blue_ml, row.dark_ml],
            })

    # Can return a max of 20 items.

    print('in catalog endpoint!')
    print('catalog is:', catalog)

    return catalog
