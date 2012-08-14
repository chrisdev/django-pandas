from django.db import DEFAULT_DB_ALIAS
from pandas.io.sql import _safe_fetch
from pandas import *

def dataframe_from_qs(qs, database_name=DEFAULT_DB_ALIAS, coerce_float=True):
    """
    """
    # Generate query, and sanitize it
    sql = str(qs.query.get_compiler(database_name).as_sql())
    
    # Fetch data
    compiler = qs.query.get_compiler(DEFAULT_DB_ALIAS)
    rows = compiler.execute_sql()
    
    # Fetch column names
    col_count = 0
    columns = [col_desc.replace('"','').replace('.','_') for col_desc in compiler.get_columns()]
    
    # Generate Dataframe
    df = DataFrame.from_records(rows.next(), columns=columns, coerce_float=True)
    return df







