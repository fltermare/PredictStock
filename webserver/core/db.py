from . import database


def get_available_stock():
    sql_cmd = """
        SELECT *
        FROM stock
    """
    query_data = database.engine.execute(sql_cmd)
    print(query_data)
    res = query_data.fetchall()

    return str(res)
