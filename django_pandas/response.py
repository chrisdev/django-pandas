from django.http.response import HttpResponse


class PandasJsonResponse(HttpResponse):
    """
    An easier way to return a json encoded response from
    'Pandas.to_dataframe().to_json()' object
    """

    def __init__(self, data, **kwargs):
        data = data.reset_index().to_json(orient='records', date_format='iso')
        kwargs.setdefault('content_type', 'application/json')
        super().__init__(content=data, **kwargs)
        