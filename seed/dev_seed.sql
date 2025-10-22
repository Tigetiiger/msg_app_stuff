INSERT INTO users (email, name) VALUES
  ('alice@example.test', 'Alice'),
  ('bob@example.test', 'Bob')
ON CONFLICT DO NOTHING;
