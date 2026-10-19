# Local Setup

Instructions for running the project locally on Windows using PowerShell.

## Prerequisites

- Git
- Python 3.12 (developed with 3.12.10)
- PostgreSQL and pgAdmin

## 1. Clone the Repository

```powershell
git clone https://github.com/sutomuz/Nguyen-Johnathan-Stock-Market-Dashboard.git
cd Nguyen-Johnathan-Stock-Market-Dashboard
```

All commands below specify whether to run from the repository root or `app/`.

## 2. Install Python Dependencies

From the repository root:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r app/requirements.txt
```

Keep `.venv` at the repository root. It is excluded from Git.

## 3. Create the Database

In pgAdmin:

1. Connect to your local PostgreSQL server.
2. Create a database named `stock_dashboard`.
3. Open the Query Tool for that database.
4. Open and execute `app/scripts/database/schema.sql`.

Run the schema on a new, empty database. It creates the `securities`
and `daily_prices` tables.

## 4. Configure the Connection

From the repository root:

```powershell
Copy-Item .env.example .env
```

If `.env` already exists, keep your existing configuration instead of
overwriting it.

Edit `.env` with your local connection settings:

```dotenv
DB_HOST=localhost
DB_PORT=5432
DB_NAME=stock_dashboard
DB_USER=postgres
DB_PASSWORD='your_local_password'
```

The local development setup uses `postgres`. Deployment should use
appropriately restricted database permissions.

Never commit `.env` or actual passwords. `.env.example` contains only
placeholder settings and is safe to track.

Check the connection:

```powershell
cd app
..\.venv\Scripts\python.exe scripts/database/check_connection.py
```

Expected database: `stock_dashboard`.

## 5. Add the Source Dataset

Place the source files at the repository root in this layout:

```text
data/raw/
├── symbols_valid_meta.csv
├── stocks/
│   └── [symbol].csv
└── etfs/
    └── [symbol].csv
```

The dataset is not included in Git. Its source download link and
licensing details still need to be documented.

## 6. Inspect and Clean the Data

From `app/`:

```powershell
..\.venv\Scripts\python.exe scripts/preprocessing/inspect_data.py
..\.venv\Scripts\python.exe scripts/preprocessing/audit_data.py
..\.venv\Scripts\python.exe scripts/preprocessing/check_flagged_rows.py
..\.venv\Scripts\python.exe scripts/preprocessing/clean_data.py
..\.venv\Scripts\python.exe scripts/preprocessing/clean_metadata.py
```

Review each script's output before continuing.

Cleaned datasets are written to `data/processed/`.
Audit and cleaning reports are written to `docs/reports/`.

Verify price-file mappings:

```powershell
..\.venv\Scripts\python.exe scripts/database/check_price_matches.py
```

For the current dataset, the expected result is 8,049 processed price
files with zero unmatched files.

## 7. Import the Data

From `app/`, load metadata before prices:

```powershell
..\.venv\Scripts\python.exe scripts/database/load_securities.py
..\.venv\Scripts\python.exe scripts/database/load_prices.py
```

The price import processes millions of records and prints progress.

Expected counts for the current cleaned dataset:

| Table | Records |
|---|---:|
| securities | 8,049 |
| daily_prices | 28,151,075 |

Rerunning the price loader replaces each imported security's existing
price history with its processed file.

Cleaning and importing are initial setup steps. They are not required
every time the project is opened.

## 8. Run Backend Examples

From `app/`:

```powershell
# Search and security details
..\.venv\Scripts\python.exe -m backend.securities

# Historical prices
..\.venv\Scripts\python.exe -m backend.prices

# Returns and volatility
..\.venv\Scripts\python.exe -m backend.analytics

# Selected-security comparisons
..\.venv\Scripts\python.exe -m backend.comparisons
..\.venv\Scripts\python.exe -m backend.performance

# Market-wide rankings
..\.venv\Scripts\python.exe -m backend.rankings
..\.venv\Scripts\python.exe -m backend.volatility_rankings

# Supported ranking question
..\.venv\Scripts\python.exe -m backend.answers
```

These commands use demonstration inputs defined in each module.

## 9. Run Tests

From `app/`:

```powershell
..\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

The current suite contains 15 tests covering calculations, missing
prices, comparison intervals, question parsing, and routing.

These tests use sample data and mocks. They do not require a populated
database and do not verify every source record.

## Returning to the Project

1. Open the repository folder in Cursor.
2. Ensure the PostgreSQL service is running.
3. Open a terminal at the repository root.
4. Enter `cd app` before running backend commands.

There is no need to recreate the environment or reimport existing data.
Closing pgAdmin does not normally stop the PostgreSQL service.

Dashboard launch instructions will be added when the interface is built.

## Troubleshooting

### Database connection fails

Check that PostgreSQL is running and that the root `.env` contains the
correct host, port, database, username, and password.

### Python cannot find the backend package

Run module commands from `app/`, using `-m`:

```powershell
..\.venv\Scripts\python.exe -m backend.securities
```

### Cursor shows unresolved backend imports

Open the repository root as the workspace. The root
`pyrightconfig.json` configures `app/` as the Python source root.

### Git displays a long output screen

Press `q` to exit Git's output viewer. To avoid it for status and diffs:

```powershell
git --no-pager status --short
git --no-pager diff --stat
```