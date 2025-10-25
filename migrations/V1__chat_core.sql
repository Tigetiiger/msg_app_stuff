-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 0) Helpful: app schema (optional)
CREATE SCHEMA IF NOT EXISTS app;
SET search_path TO app, public;

-- 1) Users
CREATE TABLE IF NOT EXISTS app.users (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  username      TEXT NOT NULL UNIQUE,
  display_name  TEXT,
  mail TEXT,
  password_hash TEXT NOT NULL,
  password_updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2) Conversations (DMs & Groups)
-- conversation_type: 1=dm, 2=group  (INT over ENUM => easier migrations)
CREATE TABLE IF NOT EXISTS app.conversations (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  type          SMALLINT NOT NULL CHECK (type IN (1, 2)),
  created_by    UUID NOT NULL REFERENCES app.users(id),
  title         TEXT,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  last_written_to TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 3) Participants (membership)
-- participant_role: 1=member, 2=admin, 3=owner
CREATE TABLE IF NOT EXISTS app.conversation_participants (
  conversation_id UUID NOT NULL,
  user_id         UUID NOT NULL,
  role            SMALLINT NOT NULL DEFAULT 1 CHECK (role IN (1, 2, 3)),
  joined_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (conversation_id, user_id),
  CONSTRAINT fk_participant_convo
    FOREIGN KEY (conversation_id) REFERENCES app.conversations(id) ON DELETE CASCADE,
  CONSTRAINT fk_participant_user
    FOREIGN KEY (user_id)        REFERENCES app.users(id)         ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_participants_user
  ON app.conversation_participants (user_id);

-- 4) Messages (single table for all chats)
CREATE TABLE IF NOT EXISTS app.messages (
  id               BIGSERIAL PRIMARY KEY,
  conversation_id  UUID NOT NULL REFERENCES app.conversations(id) ON DELETE CASCADE,
  sender_id        UUID NOT NULL REFERENCES app.users(id),
  body             TEXT NOT NULL,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  edited_at        TIMESTAMPTZ,
  deleted_at       TIMESTAMPTZ
);

-- Ensure only participants can send messages
ALTER TABLE app.messages
  ADD CONSTRAINT fk_sender_in_convo
  FOREIGN KEY (conversation_id, sender_id)
  REFERENCES app.conversation_participants (conversation_id, user_id);

-- Paging & retrieval indexes
CREATE INDEX IF NOT EXISTS idx_messages_convo_created_at
  ON app.messages (conversation_id, created_at);
CREATE INDEX IF NOT EXISTS idx_messages_convo_id
  ON app.messages (conversation_id, id);

-- 5) (Optional now, but common) unique DM constraint:
-- If you want one DM per user pair, add a deterministic key in conversations.metadata later.
