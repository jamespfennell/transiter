-- +goose Up

ALTER TABLE feed DROP COLUMN update_period;
ALTER TABLE feed DROP COLUMN update_strategy;
