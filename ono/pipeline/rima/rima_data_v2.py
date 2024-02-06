import argparse
import os
import uuid
import psycopg2
import psycopg2.extras
import pandas as pd

from datetime import datetime
from uuid import uuid4
from sshtunnel import SSHTunnelForwarder
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from typing import List, Optional, Set

from ner.natasha.client import NatashaClient, MODEL_NAME
from pipeline.rima.queries import (
    INSERT_ARTICLE_QUERY,
    INSERT_ARTICLE_X_ENTITY_QUERY,
    INSERT_ENTITY_QUERY,
    SELECT_RIMA_RAW_QUERY,
    SELECT_ENTITIES_DICT_QUERY,
)
from pipeline.config import (
    SOURCE_SLUG_MAPPER,
    RIMA_SOURCE_STR,
)
from pipeline.utils import source_slug_mapper_maker

parser = argparse.ArgumentParser()
parser.add_argument("--pg_host", default="localhost")
parser.add_argument("--pg_port", default="5432")
parser.add_argument("-f", "--file", required=False, help="JSON file name")
parser.add_argument("-s", "--source", required=False, default=RIMA_SOURCE_STR)
parser.add_argument("-y", "--year", required=True, type=int)

args = parser.parse_args()
args_vars = vars(args)

RIMA_BASE_KEY = "RIMA"
SSH_HOST = "bastion.de.rima.media"
SSH_PRIVATE_KEY = "~/.ssh/id_rsa"
SSH_USERNAME = "rmalushkin"
SSH_BIND_ADDRESS = "rima-de.cluster-cuacljzqucw0.us-west-2.rds.amazonaws.com"
POSTGRE_DATABASE = "rima_ext"
POSTGRE_USER = os.environ["POSTGRE_USER"]
POSTGRE_PASSWORD = os.environ["POSTGRE_PASSWORD"]
POSTGRE_CONFIG = {
    "user": POSTGRE_USER,
    "password": POSTGRE_PASSWORD,
    "host": args_vars["pg_host"],
    "port": args_vars["pg_port"],
}
SOURCE_SET = set(args_vars["source"].split(" "))
SOURCE_SLUG_MAPPER_DATA = source_slug_mapper_maker(SOURCE_SLUG_MAPPER)
YEAR = args_vars["year"]

psycopg2.extras.register_uuid()


def execute_query(query, vars=None) -> Optional[List]:
    cursor.execute(query, vars)
    return cursor.fetchall() if cursor.pgresult_ptr else None


def get_raw_data(source_name) -> List[tuple]:
    _query = SELECT_RIMA_RAW_QUERY.format(
        schema="public", table="parsed_web_content", year=YEAR, s=source_name
    )
    return execute_query(_query)


def extract_ner(text) -> Set:
    """

    :param text:
    :return:
    """
    ner_obj = NatashaClient(f"А {text}")
    return ner_obj.ner()


def drop_dupl_data(entity_batch, article_x_entity_batch) -> (list, list):
    """

    :param entity_batch:
    :param article_x_entity_batch:
    :return:
    """
    entity_cols = ["entity_id", "model", "tag", "name"]
    article_x_entity_cols = ["article_id", "entity_id", "is_title"]

    entity_batch_pd = pd.DataFrame.from_records(entity_batch, columns=entity_cols)
    entity_batch_dd_pd = entity_batch_pd.drop_duplicates(entity_cols[1:], keep="last")

    entity_batch_mapper_pd = entity_batch_pd.merge(
        entity_batch_dd_pd,
        how="left",
        on=entity_cols[1:],
        suffixes=("", "_actual"),
    )[["entity_id", "entity_id_actual"]]

    article_x_entity_batch_pd = pd.DataFrame.from_records(
        article_x_entity_batch,
        columns=article_x_entity_cols,
    )

    article_x_entity_batch_actual_pd = (
        article_x_entity_batch_pd.merge(
            entity_batch_mapper_pd,
            how="left",
            on="entity_id",
        )
        .drop("entity_id", axis=1)
        .rename(columns={"entity_id_actual": "entity_id"})[article_x_entity_cols]
    )

    return (
        entity_batch_dd_pd.to_records(index=None).tolist(),
        article_x_entity_batch_actual_pd.to_records(index=None).tolist(),
    )


def process_article_ner(
    article_id: uuid.UUID,
    ner_data: Set,
    is_title: bool,
    article_x_entity_batch: List,
    entity_batch: List,
):
    """

    :param article_id:
    :param ner_data:
    :param is_title:
    :param article_x_entity_batch:
    :param entity_batch:
    :return:
    """

    for ner_item in ner_data:
        entity_id = uuid4()
        entity = (
            entity_id,
            MODEL_NAME,  # model
            ner_item[0],  # tag
            ner_item[1].replace("'", "''"),  # name
        )
        entity_batch.append(entity)

        article_x_entity = (article_id, entity_id, is_title)
        article_x_entity_batch.append(article_x_entity)


def process_source_article_batch(data_batch, params):
    article_batch = []
    article_x_entity_batch = []
    entity_batch = []

    for item in data_batch:
        try:
            article_id = uuid4()
            article = (
                article_id,
                item[2],
                item[4],
                item[3],
                item[6],
                SOURCE_SLUG_MAPPER_DATA[item[1]],
                item[5],
                RIMA_BASE_KEY,
                item[0],
            )
            article_batch.append(article)

            # Title and plain text NER processing
            for is_title, text in [(True, item[2]), (False, item[4])]:
                article_ner_data = extract_ner(text)
                process_article_ner(
                    article_id,
                    article_ner_data,
                    is_title,
                    article_x_entity_batch,
                    entity_batch,
                )

        except Exception as e:
            print(f"Error processing article {item[0]}: {e}")

    entity_batch, article_x_entity_batch = drop_dupl_data(
        entity_batch, article_x_entity_batch
    )

    with psycopg2.connect(**params) as local_conn:
        with local_conn.cursor() as local_cursor:
            local_cursor.executemany(INSERT_ARTICLE_QUERY, article_batch)
            local_cursor.executemany(INSERT_ENTITY_QUERY, entity_batch)
            local_cursor.executemany(INSERT_ARTICLE_X_ENTITY_QUERY, article_x_entity_batch)
            local_conn.commit()


if __name__ == "__main__":
    while SOURCE_SET:
        source = SOURCE_SET.pop()

        with SSHTunnelForwarder(
            (SSH_HOST, 22),
            ssh_private_key=SSH_PRIVATE_KEY,
            ssh_username=SSH_USERNAME,
            remote_bind_address=(SSH_BIND_ADDRESS, 5432),
        ) as ssh:
            ssh.start()

            params = POSTGRE_CONFIG.copy()
            params["port"] = ssh.local_bind_port
            params["dbname"] = "rima_de"

            with psycopg2.connect(**params) as connection:
                with connection.cursor() as cursor:
                    data = get_raw_data(source)[:200]

            batch_size = 1000
            data_batches = [
                data[i : i + batch_size] for i in range(0, len(data), batch_size)
            ]

            params["dbname"] = "rima_ext"

            print(f"Processing {len(data)} items from source `{source}`...")

            with ThreadPoolExecutor(max_workers=32) as executor:
                list(
                    executor.map(
                        lambda batch: process_source_article_batch(batch, params),
                        data_batches,
                    )
                )

            print(f"Completed processing items from source `{source}`")

            ssh.stop()
