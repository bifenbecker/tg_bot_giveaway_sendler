from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "telegramchat" (
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "type" VARCHAR(50) NOT NULL,
    "title" VARCHAR(128),
    "username" VARCHAR(100),
    "first_name" VARCHAR(100),
    "last_name" VARCHAR(100),
    "bio" TEXT,
    "description" TEXT,
    "invite_link" VARCHAR(200)
);
CREATE TABLE IF NOT EXISTS "telegramuser" (
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "username" VARCHAR(32)  UNIQUE,
    "is_bot" BOOL NOT NULL  DEFAULT False,
    "first_name" VARCHAR(64),
    "last_name" VARCHAR(64),
    "language_code" VARCHAR(10),
    "bot_admin" BOOL NOT NULL  DEFAULT False,
    "bot_mailing" BOOL NOT NULL  DEFAULT True,
    "from_app" VARCHAR(50) NOT NULL  DEFAULT 'bot',
    "bad" BOOL NOT NULL  DEFAULT False,
    "last_check" TIMESTAMPTZ,
    "is_active" BOOL
);
CREATE TABLE IF NOT EXISTS "giveaway" (
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "id" SERIAL NOT NULL PRIMARY KEY,
    "name" VARCHAR(100) NOT NULL UNIQUE,
    "active" BOOL NOT NULL  DEFAULT True,
    "author_id" BIGINT NOT NULL REFERENCES "telegramuser" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "giveawaymember" (
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "id" SERIAL NOT NULL PRIMARY KEY,
    "checked_time" TIMESTAMPTZ,
    "giveaway_id" INT NOT NULL REFERENCES "giveaway" ("id") ON DELETE CASCADE,
    "user_id" BIGINT NOT NULL REFERENCES "telegramuser" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_giveawaymem_user_id_08d962" UNIQUE ("user_id", "giveaway_id")
);
CREATE TABLE IF NOT EXISTS "giveawaymemberchecktimes" (
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "id" SERIAL NOT NULL PRIMARY KEY,
    "check_time" TIMESTAMPTZ NOT NULL,
    "finish" BOOL NOT NULL  DEFAULT False,
    "giveaway_id" INT NOT NULL REFERENCES "giveaway" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_giveawaymem_check_t_97708b" UNIQUE ("check_time", "giveaway_id")
);
CREATE TABLE IF NOT EXISTS "giveawaysponsor" (
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "id" SERIAL NOT NULL PRIMARY KEY,
    "username" VARCHAR(100) NOT NULL,
    "ok_permissions" BOOL NOT NULL  DEFAULT False,
    "chat_id" BIGINT NOT NULL REFERENCES "telegramchat" ("id") ON DELETE CASCADE,
    "giveaway_id" INT NOT NULL REFERENCES "giveaway" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_giveawayspo_chat_id_3ae895" UNIQUE ("chat_id", "giveaway_id")
);
CREATE TABLE IF NOT EXISTS "mailing" (
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "id" SERIAL NOT NULL PRIMARY KEY,
    "name" VARCHAR(200),
    "tg_message_id" BIGINT NOT NULL,
    "status" VARCHAR(11) NOT NULL,
    "exclude_members" BOOL NOT NULL  DEFAULT True,
    "author_id" BIGINT NOT NULL REFERENCES "telegramuser" ("id") ON DELETE CASCADE,
    "giveaway_id" INT REFERENCES "giveaway" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_mailing_giveawa_66a6c1" UNIQUE ("giveaway_id", "name")
);
COMMENT ON COLUMN "mailing"."status" IS 'wait: wait\nin_progress: in_progress\npaused: paused\ncompleted: completed';
CREATE TABLE IF NOT EXISTS "mailinguserlistreport" (
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "id" SERIAL NOT NULL PRIMARY KEY,
    "status" VARCHAR(7) NOT NULL,
    "tg_message_id" BIGINT,
    "mailing_id" INT NOT NULL REFERENCES "mailing" ("id") ON DELETE CASCADE,
    "user_id" BIGINT NOT NULL REFERENCES "telegramuser" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_mailinguser_mailing_6ada5a" UNIQUE ("mailing_id", "user_id")
);
COMMENT ON COLUMN "mailinguserlistreport"."status" IS 'queued: queued\nerror: error\nsuccess: success';
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSONB NOT NULL
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """
