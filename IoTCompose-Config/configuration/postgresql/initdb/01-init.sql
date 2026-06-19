CREATE USER chirpstack WITH PASSWORD 'chirpstack';
CREATE DATABASE chirpstack OWNER chirpstack;
\c chirpstack chirpstack
CREATE EXTENSION IF NOT EXISTS pg_trgm;
