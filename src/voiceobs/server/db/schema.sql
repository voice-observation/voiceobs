-- Database schema for voiceobs
-- This schema stores voice conversation telemetry data

-- Conversations table: groups of related spans representing a single conversation
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id VARCHAR(255) NOT NULL UNIQUE,  -- External conversation ID from spans
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_conversations_conversation_id ON conversations(conversation_id);
CREATE INDEX IF NOT EXISTS idx_conversations_created_at ON conversations(created_at);

-- Spans table: individual telemetry spans
CREATE TABLE IF NOT EXISTS spans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE,
    end_time TIMESTAMP WITH TIME ZONE,
    duration_ms DOUBLE PRECISION,
    attributes JSONB NOT NULL DEFAULT '{}',
    trace_id VARCHAR(64),
    span_id VARCHAR(64),
    parent_span_id VARCHAR(64),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_spans_name ON spans(name);
CREATE INDEX IF NOT EXISTS idx_spans_trace_id ON spans(trace_id);
CREATE INDEX IF NOT EXISTS idx_spans_conversation_id ON spans(conversation_id);
CREATE INDEX IF NOT EXISTS idx_spans_created_at ON spans(created_at);
CREATE INDEX IF NOT EXISTS idx_spans_attributes ON spans USING GIN(attributes);

-- Turns table: voice conversation turns extracted from spans
CREATE TABLE IF NOT EXISTS turns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    turn_id VARCHAR(255),  -- External turn ID from span attributes
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    span_id UUID NOT NULL REFERENCES spans(id) ON DELETE CASCADE,
    actor VARCHAR(50) NOT NULL,  -- 'user', 'agent', 'system'
    turn_index INTEGER,
    duration_ms DOUBLE PRECISION,
    transcript TEXT,
    attributes JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_turns_conversation_id ON turns(conversation_id);
CREATE INDEX IF NOT EXISTS idx_turns_turn_id ON turns(turn_id);
CREATE INDEX IF NOT EXISTS idx_turns_actor ON turns(actor);
CREATE INDEX IF NOT EXISTS idx_turns_turn_index ON turns(turn_index);

-- Failures table: detected failures in conversations
CREATE TABLE IF NOT EXISTS failures (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    failure_type VARCHAR(50) NOT NULL,  -- e.g., 'interruption', 'excessive_silence'
    severity VARCHAR(20) NOT NULL,  -- 'low', 'medium', 'high'
    message TEXT NOT NULL,
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    turn_id UUID REFERENCES turns(id) ON DELETE SET NULL,
    turn_index INTEGER,
    signal_name VARCHAR(100),
    signal_value DOUBLE PRECISION,
    threshold DOUBLE PRECISION,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_failures_failure_type ON failures(failure_type);
CREATE INDEX IF NOT EXISTS idx_failures_severity ON failures(severity);
CREATE INDEX IF NOT EXISTS idx_failures_conversation_id ON failures(conversation_id);
CREATE INDEX IF NOT EXISTS idx_failures_created_at ON failures(created_at);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to auto-update updated_at for conversations
DROP TRIGGER IF EXISTS update_conversations_updated_at ON conversations;
CREATE TRIGGER update_conversations_updated_at
    BEFORE UPDATE ON conversations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
