SELECT_ALL_QUERY = "SELECT * FROM {schema}.{table} WHERE source='{s}' AND is_processed=false"
# _HELP_SELECT_ALL_QUERY = "SELECT * FROM {table} WHERE source='Lenta.ru' AND title='Бывшая жена богатейшего человека мира на время стала богатейшей женщиной планеты'"

SELECT_SPEC_ENTITY_QUERY = "SELECT * FROM {schema}.{table} WHERE model='{m}' AND tag='{t}' AND name='{n}'"

# INSERT_ARTICLE_QUERY = "INSERT INTO ono.article(article_id, title, plain_text, published_dt, link_url, source_slug) VALUES(%s, %s, %s, %s, %s, %s);"
INSERT_ONO_ARTICLE_QUERY = """
INSERT INTO ono.article(article_id, title, plain_text, published_dt, link_url, source_slug, base, base_article_id) 
VALUES(%s, %s, %s, %s, %s, %s, %s, %s);"""

INSERT_ENTITY_QUERY = "INSERT INTO ono.entity(entity_id, model, tag, name) VALUES(%s, %s, %s, %s);"
INSERT_ARTICLE_X_ENTITY_QUERY = "INSERT INTO ono.article_x_entity(article_id, entity_id, is_title) VALUES(%s, %s, %s);"

UPDATE_PROCESSED_QUERY = "UPDATE {schema}.{table} SET is_processed=true WHERE ono_id={id}"