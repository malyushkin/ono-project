create table article
(
    article_id      uuid not null
        constraint article_pk
            primary key,
    rima_article_id integer,
    title           text,
    plain_text      text,
    published_dt    date
);

alter table article
    owner to server;

create table entity
(
    entity_id uuid not null
        constraint entity_pk
            primary key,
    tag       varchar(32),
    name      varchar(256)
);

alter table entity
    owner to server;

create table entity_attribute
(
    entity_id uuid
        constraint entity_fk
            references entity
            on update cascade on delete cascade,
    key       varchar(32),
    value     varchar(256)
);

alter table entity_attribute
    owner to server;

create table article_x_entity
(
    article_id uuid
        constraint article_fk
            references article
            on update cascade on delete cascade,
    entity_id  uuid
        constraint entity_fk
            references entity
);

alter table article_x_entity
    owner to server;

