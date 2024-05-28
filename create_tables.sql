CREATE TABLE users (
    user_id UUID,                     -- Unique identifier for the user
    username String,                  -- User's chosen username
    hashed_password String,           -- Hashed password for authentication
    status String                     -- Additional status or user information
) ENGINE = MergeTree()
ORDER BY (user_id);


CREATE TABLE chat_messages (
    message_id UUID,                  -- Unique identifier for the message
    user_id UUID,                     -- ID of the user who sent the message
    session_id UUID,                  -- ID of the chat session
    timestamp DateTime,               -- When the message was sent
    message_content String,           -- The text content of the message
    metadata Nullable(String)         -- JSON string to store additional metadata (e.g., device info, message type)
) ENGINE = MergeTree()
ORDER BY (session_id, timestamp);


CREATE TABLE chat_sessions (
    session_id UUID,                  -- Unique identifier for the session
    start_time DateTime,              -- Start time of the session
    end_time Nullable(DateTime),      -- End time of the session, if applicable
    metadata Nullable(String)         -- JSON string to store additional metadata about the session
) ENGINE = MergeTree()
ORDER BY (start_time);
