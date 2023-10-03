from pullenti_client import Client
from pullenti_client.referent import Referent, Slot
from pullenti_client.result import Match, Result

import pandas as pd
from typing import Any, Optional, List, Union


class PullentiAnalyzer:
    PULLENTI_KEYS = {"GEO", "ORGANIZATION", "PERSON"}
    GEO_RULES = {"NA": "name"}
    ORGANIZATION_RULES = {"NA": "name"}
    PERSON_RULES = {"NA": "lastname"}

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
        check_na = [column for column in rules["NA"] if column in dataframe.columns]
        check_vars = [column for column in dataframe.columns if "_vars" not in column]

        if any(check_na):
            dataframe.dropna(subset=rules["NA"], how="any", inplace=True)
        if check_vars:
            dataframe.drop_duplicates(subset=check_vars, inplace=True)

        dataframe.dropna(how="all", axis=1, inplace=True)

        if rules["NA"] not in dataframe.columns:
            return pd.DataFrame(data=[])

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
            return pd.DataFrame(data=[])

        data: list[dict] = []

        for slots in self.slots(analyzer):
            ner_row = {"tag": analyzer}

            for slot in slots:
                if slot.key.lower() == ["attribute", "higher"]:
                    continue
                if slot.key.lower() not in ner_row and type(slot.value) is not Referent:
                    ner_row[slot.key.lower()] = slot.value
                elif slot.key.lower() + "_vars" not in ner_row and type(
                        slot.value) is not Referent:
                    ner_row[slot.key.lower() + "_vars"] = [slot.value]
                elif slot.key.lower() + "_vars" in ner_row and type(
                        slot.value) is not Referent:
                    ner_row[slot.key.lower() + "_vars"].append(slot.value)

            data.append(ner_row)

        dataframe = pd.DataFrame.from_dict(data=data)

        if analyzer == "GEO":
            dataframe = self._data_helper(dataframe, self.GEO_RULES)
        elif analyzer == "ORGANIZATION":
            dataframe = self._data_helper(dataframe, self.ORGANIZATION_RULES)
        elif analyzer == "PERSON":
            dataframe = self._data_helper(dataframe, self.PERSON_RULES)

        return dataframe
