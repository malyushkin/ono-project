from pullenti_client import Client
from pullenti_client.referent import Referent, Slot
from pullenti_client.result import Match, Result

import pandas as pd
from typing import Any, Optional, List, Union

some_text = """
Министр внутренних дел федеральной земли Бранденбург Михаэль Штюбген обеспокоен все 
менее контролируемой ситуацией с наплывом нелегальных мигрантов через границу с 
соседней Польшей. "Ситуация на границе систематически ухудшается уже многие месяцы. 
В результате число новоприбывших, регистрируемых в приемных центрах Бранденбурга, 
значительно выросло", - заявил он в интервью газете Neue Osnabrücker Zeitung, 
обнародованном в субботу, 16 сентября.

По словам Штюбгена, сейчас федеральная полиция ежедневно направляет в приемный центр в 
среднем по 58 мигрантов, тогда как только в июле ежедневное число предполагаемых 
нелегалов составляло 22 человека.
"""


class PullentiAnalyzer:
    PULLENTI_KEYS = {"GEO", "ORGANIZATION", "PERSON"}
    GEO_RULES = {"NA": ["name", "type"]}
    ORGANIZATION_RULES = {"NA": ["name"]}
    PERSON_RULES = {"NA": ["lastname"]}

    def __init__(
            self,
            text: str,
            analyzers: Optional[List[str]] = None,
            params_kwargs: Optional[dict] = None
    ):
        """
        Args:
            text:
            analyzers:
        Returns:
            A new cursor object using the connection
        """

        self.text = text
        self.analyzers = analyzers if analyzers else self.PULLENTI_KEYS
        self.pullenti_client = None

        # Check analyzers
        if analyzers:
            if not all(key in analyzers for key in self.PULLENTI_KEYS):
                raise KeyError

        # Init pullenti
        try:
            self.pullenti_client = Client(**params_kwargs)
            self.pullenti_client.__call__("test")
        except Exception:
            raise Exception

    @staticmethod
    def _append_matches(matches: list, match: Match, analyzer: Optional[str]):
        if analyzer:
            if match.referent.label == analyzer:
                matches.append(match)
        else:
            matches.append(match)
        return matches

    @staticmethod
    def _data_helper(dataframe: pd.DataFrame, rules):
        dataframe.dropna(subset=rules["NA"], how="any", inplace=True)
        dataframe.dropna(how="all", axis=1, inplace=True)
        dataframe.drop_duplicates(subset=rules["NA"], inplace=True)
        return dataframe

    def result(self) -> Result:
        return self.pullenti_client(self.text)

    def matches(self, analyzer: Optional[str] = None) -> Optional[List[Match]]:
        matches = []
        for match in self.result().matches:
            matches = self._append_matches(matches, match, analyzer)
            for child_match in match.children:
                matches = self._append_matches(matches, child_match, analyzer)
        return matches

    def slots(self, analyzer: Optional[str]) -> Optional[List[Slot]]:
        return [match.referent.slots for match in self.matches(analyzer)]

    def data(self, analyzer: Optional[str]) -> Optional[pd.DataFrame]:
        if not self.slots(analyzer):
            return None

        data: list[dict] = []

        for slots in self.slots(analyzer):
            ner_row = {"tag": analyzer}

            for slot in slots:
                if slot.key.lower() not in ner_row:
                    ner_row[slot.key.lower()] = slot.value
                elif slot.key.lower() + "_vars" not in ner_row:
                    ner_row[slot.key.lower() + "_vars"] = [slot.value]
                elif slot.key.lower() + "_vars" in ner_row:
                    ner_row[slot.key.lower() + "_vars"].append(slot.value)

                if slot.key.lower() == "attribute":
                    attributes = [
                        slot.value for slot in slot.value.slots
                        if type(slot.value) is not Referent
                    ]

                    ner_row[slot.key.lower() + "_vars"] = attributes
                    del ner_row[slot.key.lower()]

            if "higher" not in ner_row.keys():
                data.append(ner_row)

        dataframe = pd.DataFrame.from_dict(data=data)

        if analyzer == "GEO":
            dataframe = self._data_helper(dataframe, self.GEO_RULES)
        elif analyzer == "ORGANIZATION":
            dataframe = self._data_helper(dataframe, self.ORGANIZATION_RULES)
        elif analyzer == "PERSON":
            dataframe = self._data_helper(dataframe, self.PERSON_RULES)

        return dataframe


test = PullentiAnalyzer(some_text, params_kwargs={"host": "localhost", "port": 8081})
