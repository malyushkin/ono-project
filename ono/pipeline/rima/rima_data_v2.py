import argparse
import os
import uuid

import psycopg2
import psycopg2.extras
import pandas as pd
from uuid import uuid4
from sshtunnel import SSHTunnelForwarder
from concurrent.futures import ThreadPoolExecutor
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
SSH_USERNAME = "yurfakov"
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
    ner_obj = NatashaClient(f"А {text}")
    return ner_obj.ner()


def process_article_ner(
        article_id: uuid.UUID,
        ner_data: Set,
        is_title: bool,
        article_x_entity_batch: List,
        entity_batch: List,
        entities_pd: pd.DataFrame
):
    """

    :param article_id:
    :param ner_data:
    :param is_title:
    :param article_x_entity_batch:
    :param entity_batch:
    :param entities_pd:
    :return:
    """

    for ner_item in ner_data:
        ner_name = ner_item[1].replace("'", "''")
        match_pd = entities_pd[
            (entities_pd["tag"] == ner_item[0]) & (entities_pd["name"] == ner_name)
        ]

        if len(match_pd) > 1:
            raise ValueError("Multiple entity matches found")
        elif len(match_pd) == 1:
            entity_id = match_pd.iloc[0]["entity_id"]
        else:
            entity_id = uuid4()
            entity = (
                entity_id,
                MODEL_NAME,  # model
                ner_item[0],  # tag
                ner_name,  # name
            )
            entity_batch.append(entity)

        article_x_entity = (article_id, entity_id, is_title)
        article_x_entity_batch.append(article_x_entity)


def process_article_batch(data_batch, entities_pd):
    articles_batch = []
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
            articles_batch.append(article)

            # Title and plain text NER processing
            for is_title, text in [(True, item[2]), (False, item[4])]:
                article_ner_data = extract_ner(text)
                process_article_ner(
                    article_id,
                    article_ner_data,
                    is_title,
                    article_x_entity_batch,
                    entity_batch,
                    entities_pd,
                )
        except Exception as e:
            print(f"Error processing article {item[0]}: {e}")

    with psycopg2.connect(**POSTGRE_CONFIG) as local_conn:
        with local_conn.cursor() as local_cursor:
            local_cursor.executemany(INSERT_ARTICLE_QUERY, articles_batch)
            local_cursor.executemany(INSERT_ARTICLE_X_ENTITY_QUERY, article_x_entity_batch)
            local_cursor.executemany(INSERT_ENTITY_QUERY, entity_batch)
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
                    data = get_raw_data(source)

            batch_size = 1000
            data_batches = [
                data[i : i + batch_size] for i in range(0, len(data), batch_size)
            ]

            params["dbname"] = "rima_ext"

            with psycopg2.connect(**params) as connection:
                with connection.cursor() as cursor:
                    entities = execute_query(SELECT_ENTITIES_DICT_QUERY)
                    entities_pd = pd.DataFrame(
                        entities,
                        columns=["entity_id", "tag", "name"],
                    )

                print(f"Processing {len(data)} items from source `{source}`...")

                with ThreadPoolExecutor(32) as executor:
                    executor.map(
                        lambda batch: process_article_batch(batch, entities_pd),
                        data_batches,
                    )

                print(f"Completed processing items from source `{source}`")
            ssh.stop()
