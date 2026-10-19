# Cloud-Based Stock Market Analytics Dashboard

A historical market analytics platform for exploring stock and ETF prices, comparing performance, and ranking securities by return and volatility.

The project combines a PostgreSQL database, a Python analytics backend, and a keyword-based question assistant. The planned dashboard provides a trading-platform-style interface for historical data exploration.

**Author:** Johnathan Nguyen  
**Course:** CTS2375 — Cloud Infrastructure and Services  
**University:** Florida Polytechnic University

## Project Status

The backend and data-processing pipeline are implemented. Dashboard development and AWS deployment are next.

| Component | Status |
|---|---|
| Data inspection, auditing, and cleaning | Implemented |
| PostgreSQL schema and imports | Implemented |
| Security search and historical date ranges | Implemented |
| Return and volatility calculations | Implemented |
| Selected-security comparisons | Implemented |
| Market-wide rankings and review filters | Implemented |
| Keyword-based questions | Implemented |
| Interactive dashboard | Planned |
| AWS deployment | Planned |

## Features

- Search securities by ticker or company name.
- Retrieve historical prices within a selected date range.
- Calculate daily returns, total returns, and volatility.
- Compare selected securities using shared dates or return intervals.
- Rank securities with configurable result counts.
- Apply minimum data requirements to volatility rankings.
- Flag extreme daily moves and optionally exclude affected securities.
- Answer supported ranking questions using keyword matching.

Example questions:

> Show the top 5 stocks by volatility.  
> Which ETFs had the highest return?  
> List 3 stocks with the highest gains.

The assistant routes questions to analytical functions. It does not currently use an LLM.

## Planned Dashboard

| Panel | Features |
|---|---|
| Left | Searchable, clickable security list |
| Center | Interactive historical price chart, date controls, volume, and summary statistics |
| Right | Question assistant, chat history, and ranking results |

Planned chart features include line and candlestick views, hover details, zooming, and date-range selection.

## Technology

| Technology | Purpose |
|---|---|
| Python | Data processing and backend logic |
| pandas and NumPy | Data manipulation and calculations |
| PostgreSQL | Metadata and historical price storage |
| Psycopg | Python database connectivity |
| python-dotenv | Local configuration |
| unittest | Automated tests |
| Git and GitHub | Version control |
| Amazon EC2 | Planned application and database hosting |
| Amazon S3 | Planned dataset and database-backup storage |

## Repository Structure

```text
Nguyen-Johnathan-Stock-Market-Dashboard/
├── app/
│   ├── backend/                 # Database access and analytics
│   ├── dashboard/               # Dashboard interface
│   ├── scripts/
│   │   ├── database/            # Schema, imports, and checks
│   │   └── preprocessing/       # Inspection, auditing, and cleaning
│   ├── tests/                   # Automated tests
│   └── requirements.txt
├── data/                        # Local datasets; excluded from Git
│   ├── raw/
│   └── processed/
├── docs/
│   ├── LOCAL_SETUP.md
│   └── reports/
│       ├── cleaning_report.csv
│       └── data_audit.csv
├── Proposal/
│   ├── CTS2375_Proposal_Nguyen.pdf
│   └── CTS2375_Proposal_Nguyen.pptx
├── .env.example
├── .gitignore
├── pyrightconfig.json
└── README.md
```

The local `.env` and `.venv/` are excluded from version control.
Dataset files and empty directories may not appear in a fresh clone.

## Dataset

The current import contains:

- **8,049 securities:** 5,884 stock-category files and 2,165 ETF files.
- **28,151,075 cleaned price records.**
- Historical coverage extending approximately from **1962 through April 2020**, depending on the security.

Price records include dates, OHLC prices, adjusted closing prices, and volume. Metadata includes security names, ticker symbols, and exchange codes.

Large datasets remain outside Git. The dataset source link and licensing information still need to be documented.

## Data Processing

The pipeline:

1. Inspects source files and metadata.
2. Audits missing values, invalid prices, and inconsistent records.
3. Produces cleaned files while preserving quality flags and source-row identifiers.
4. Resolves metadata-to-filename symbol differences.
5. Imports metadata and prices into PostgreSQL.

Audit results are available in:

- [Data audit](docs/reports/data_audit.csv)
- [Cleaning report](docs/reports/cleaning_report.csv)

## Analytics Methods

| Metric | Method |
|---|---|
| Daily return | Adjusted close divided by previous adjusted close, minus one |
| Total return | Ending adjusted close divided by starting adjusted close, minus one |
| Daily volatility | Sample standard deviation of valid daily returns |
| Annualized volatility | Daily volatility multiplied by √252 |

Missing prices are not filled when calculating returns. Source-row gaps prevent calculations across observations removed during cleaning.

Selected-security comparisons use shared endpoint dates or return intervals. Market-wide volatility rankings use each security's available valid intervals and a configurable minimum return count.

## Local Setup

See the [Local Setup Guide](docs/LOCAL_SETUP.md) for installation, database configuration, dataset preparation, and backend commands.

## Testing

From `app/`, run:

```powershell
..\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Tests cover known calculations, invalid and missing prices, removed-row gaps, shared comparison intervals, question parsing, and routing.

The unit tests use sample data and mocks. They do not independently validate the entire source dataset.

## Limitations

- Prices are historical, not live market quotes.
- Financial statements and valuation fundamentals are not included.
- The source's non-ETF category includes instruments beyond ordinary company stocks.
- Positive adjusted prices may still contain errors or unresolved corporate actions.
- Extreme-move flags indicate a need for review; genuine market moves can also trigger them.
- Data coverage varies, and possible survivorship bias can affect conclusions.
- Annualized volatility is a historical estimate, not a forecast.
- The question assistant supports predefined patterns rather than unrestricted conversation.

## Planned Cloud Deployment

The application and PostgreSQL database will run on Amazon EC2.
Amazon S3 will store processed datasets and database backups.

The deployment plan includes restricted database access, an IAM role for required S3 access, and application logging. Cloud performance and recovery procedures will be documented during implementation.

## Roadmap

- [x] Audit and clean historical data.
- [x] Create and populate PostgreSQL tables.
- [x] Implement search, analytics, comparisons, and rankings.
- [x] Connect supported questions to analytical results.
- [ ] Build the three-panel dashboard.
- [ ] Add interactive price and volume charts.
- [ ] Connect dashboard controls and the question assistant.
- [ ] Improve instrument classification and ranking validation.
- [ ] Deploy and test on AWS.
- [ ] Document analytical findings, performance, and recovery procedures.