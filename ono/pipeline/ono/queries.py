SELECT_ALL_QUERY = "SELECT * FROM {table} WHERE source='{s}'"
# _HELP_SELECT_ALL_QUERY = "SELECT * FROM {table} WHERE source='Lenta.ru' AND title='Бывшая жена богатейшего человека мира на время стала богатейшей женщиной планеты'"

SELECT_SPEC_ENTITY_QUERY = "SELECT * FROM {table} WHERE model='{m}' AND tag='{t}' AND name='{n}'"

INSERT_ARTICLE_QUERY = "INSERT INTO article(article_id, title, plain_text, published_dt, link_url, source_slug) VALUES(%s, %s, %s, %s, %s, %s);"
INSERT_ENTITY_QUERY = "INSERT INTO entity(entity_id, model, tag, name) VALUES(%s, %s, %s, %s);"
INSERT_ARTICLE_X_ENTITY_QUERY = "INSERT INTO article_x_entity(article_id, entity_id, is_title) VALUES(%s, %s, %s);"
