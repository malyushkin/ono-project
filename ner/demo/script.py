from pullenti_client import Client
from pullenti_analyzer import PullentiAnalyzer

pullenti_client = Client("localhost", 8081)

some_text = """
Курс рубля резко вырос на слухах об экстренном совещании ЦБ
"""

analyzer = PullentiAnalyzer(some_text, params_kwargs={"host": "localhost", "port": 8081})
print(analyzer.data("GEO"))
