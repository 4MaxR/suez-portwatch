-- Bronze: PortWatch API records and reference lists loaded as-is. No filtering, no renaming.
-- {raw_dir} and {ref_dir} are filled in by suez_portwatch.warehouse.

CREATE SCHEMA IF NOT EXISTS bronze;

CREATE OR REPLACE TABLE bronze.chokepoint_transits AS
SELECT *
FROM read_json(
    '{raw_dir}/chokepoint_transits/*.json',
    format = 'array',
    sample_size = -1,
    filename = 'source_file'
);

CREATE OR REPLACE TABLE bronze.egypt_port_calls AS
SELECT *
FROM read_json(
    '{raw_dir}/egypt_port_calls/*.json',
    format = 'array',
    sample_size = -1,
    filename = 'source_file'
);

CREATE OR REPLACE TABLE bronze.ref_chokepoints AS
SELECT * FROM read_json('{ref_dir}/chokepoints.json', format = 'array', sample_size = -1);

CREATE OR REPLACE TABLE bronze.ref_egypt_ports AS
SELECT * FROM read_json('{ref_dir}/egypt_ports.json', format = 'array', sample_size = -1);
