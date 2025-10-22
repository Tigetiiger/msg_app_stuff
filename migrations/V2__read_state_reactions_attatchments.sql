SET search_path TO app, public;

-- Read state (unread counts via last read pointer)
CREATE TABLE IF NOT EXISTS app.conversation_reads (
  conversation_id  UUID NOT NULL REFERENCES app.conversations(id) ON DELETE CASCADE,
  user_id          UUID NOT NULL REFERENCES app.users(id)         ON DELETE CASCADE,
  last_read_msg_id BIGINT,
  last_read_at     TIMESTAMPTZ,
  PRIMARY KEY (conversation_id, user_id),
  CONSTRAINT fk_reads_last_msg
    FOREIGN KEY (last_read_msg_id) REFERENCES app.messages(id) ON DELETE SET NULL
);

-- Reactions
CREATE TABLE IF NOT EXISTS app.message_reactions (
  message_id  BIGINT NOT NULL REFERENCES app.messages(id) ON DELETE CASCADE,
  user_id     UUID   NOT NULL REFERENCES app.users(id)    ON DELETE CASCADE,
  emoji       TEXT   NOT NULL,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (message_id, user_id, emoji)
);

-- Attachments (store metadata/URI; binaries go to object storage)
CREATE TABLE IF NOT EXISTS app.message_attachments (
  id          BIGSERIAL PRIMARY KEY,
  message_id  BIGINT NOT NULL REFERENCES app.messages(id) ON DELETE CASCADE,
  uri         TEXT NOT NULL,
  mime_type   TEXT,
  byte_size   BIGINT
);

-- Helpful indexes
CREATE INDEX IF NOT EXISTS idx_reads_user ON app.conversation_reads (user_id);
CREATE INDEX IF NOT EXISTS idx_reactions_msg ON app.message_reactions (message_id);
CREATE INDEX IF NOT EXISTS idx_attachments_msg ON app.message_attachments (message_id);
