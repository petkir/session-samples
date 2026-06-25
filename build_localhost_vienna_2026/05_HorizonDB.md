Enable the required extensions

in Azure Portal

Parametergroup:
in Azure Portal

pg_durable;
vector;
azure_ai;
pg_fts;
pg_diskann;

shared_preload_libraries


CREATE EXTENSION IF NOT EXISTS pg_durable;
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS azure_ai;
CREATE EXTENSION IF NOT EXISTS pg_fts;
CREATE EXTENSION IF NOT EXISTS pg_diskann;

-- =============================================================================
-- SETUP: pg_fts Extension & BM25 Index
-- =============================================================================

SET search_path = public, pgfts;

CREATE EXTENSION IF NOT EXISTS pg_fts;



SELECT model_registry.model_add(
    'default-embedding',
    'https://buildlocalviennafoundry-resource.openai.azure.com/openai/v1',
    'text-embedding-3-small',
    'text-embedding-3-small',
    '2025-01-01-preview',
    'subscription-key',
    'your-Key'
);

SELECT model_registry.model_add(
    'default-chat',
    'https://buildlocalviennafoundry-resource.openai.azure.com/openai/v1',
    'gpt-4.1',
    'gpt-4.1',
    '2025-01-01-preview',
    'subscription-key',
    'your-Key'
);


Show Tabel:
public.knowledge_base

insert Statement line56:

[text](tmp/db/src/horizondb/demo-sql/setup/ai-search.sql)

772
aisearch.search

Show with existing Data:
[insert Data](tmp/db/src/horizondb/demo-sql/setup/data/product-sample-table.sql)

[show Pipeline](tmp/db/src/horizondb/demo-sql/data_graph_query.sql)