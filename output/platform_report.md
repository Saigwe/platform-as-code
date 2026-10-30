# Platform as code: guardrail report

**Summary for leadership:** every Snowflake warehouse, role, grant and scheduled dbt job is defined in code and
reviewed like any other change. Production spend is **capped at $2,010 a month** and dev at
**$360**: warehouses suspend automatically at their limit, so a runaway query cannot become a surprise
bill. Rebuilding an environment is one `terraform apply` and one `kubectl apply -k`, not a week of console clicks.

## Spending caps by environment

### prod

| Warehouse | Size | Auto-suspend | Monthly credit cap | Spend cap | Used by |
|---|---|---|---|---|---|
| PROD_TRANSFORM_WH | MEDIUM (4 cr/h) | 60s | 300 | $900 | PROD_TRANSFORMER |
| PROD_REPORTING_WH | SMALL (2 cr/h) | 300s | 250 | $750 | PROD_REPORTER |
| PROD_LOADING_WH | XSMALL (1 cr/h) | 60s | 120 | $360 | PROD_LOADER |

Capped at **670 credits ($2,010) a month**, inside the 800 credit budget.
### dev

| Warehouse | Size | Auto-suspend | Monthly credit cap | Spend cap | Used by |
|---|---|---|---|---|---|
| DEV_TRANSFORM_WH | XSMALL (1 cr/h) | 60s | 60 | $180 | DEV_TRANSFORMER |
| DEV_REPORTING_WH | XSMALL (1 cr/h) | 60s | 30 | $90 | DEV_REPORTER |
| DEV_LOADING_WH | XSMALL (1 cr/h) | 60s | 30 | $90 | DEV_LOADER |

Capped at **120 credits ($360) a month**, inside the 150 credit budget.

## Guardrail results

| Check | Result |
|---|---|
| terraform code | pass |
| docker image | pass |
| dev warehouses | pass |
| dev kubernetes | pass |
| prod warehouses | pass |
| prod kubernetes | pass |

## What the guardrails block

A pull request that adds this to dev (an XLARGE warehouse, hourly auto-suspend and ACCOUNTADMIN access) is rejected
before it merges:

- dev/TRANSFORM: XLARGE is larger than the SMALL allowed in dev
- dev/TRANSFORM: auto-suspend of 3600s bills idle time (max 300s)
- dev/TRANSFORM: ACCOUNTADMIN must not be granted warehouse access directly
- dev: credit caps total 900, over the 150 credit budget ($2,700 vs $450)
