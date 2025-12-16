-- Migration: 010_extend_revision_trigger_enum
-- Feature: 005-mental-models
--
-- Align database enum with code/tests by adding additional revision triggers.

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'revision_trigger') THEN
        -- Add 'user_request' if missing
        IF NOT EXISTS (
            SELECT 1
            FROM pg_enum e
            JOIN pg_type t ON t.oid = e.enumtypid
            WHERE t.typname = 'revision_trigger'
              AND e.enumlabel = 'user_request'
        ) THEN
            ALTER TYPE revision_trigger ADD VALUE 'user_request';
        END IF;

        -- Add 'new_memory' if missing
        IF NOT EXISTS (
            SELECT 1
            FROM pg_enum e
            JOIN pg_type t ON t.oid = e.enumtypid
            WHERE t.typname = 'revision_trigger'
              AND e.enumlabel = 'new_memory'
        ) THEN
            ALTER TYPE revision_trigger ADD VALUE 'new_memory';
        END IF;
    END IF;
END
$$;

