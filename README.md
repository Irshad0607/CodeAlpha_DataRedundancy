# Data Redundancy Removal System
### CodeAlpha Cloud Computing Internship — Task 1

## Live Demo
**https://codealpha-dedup-app.azurewebsites.net**

## Project Overview

A cloud-based Data Redundancy Removal System that detects and prevents duplicate data entries using SHA-256 hashing and Azure Cosmos DB.

## Task Requirements Satisfied

| Requirement | Implementation |
|---|---|
| Identify & classify redundant data | SHA-256 hashing classifies data as UNIQUE or REDUNDANT |
| Validation mechanism | All incoming data is normalized and hash-compared |
| Prevent duplicate entries | Duplicates rejected at API level before database write |
| Append only unique entries | Only hash-verified unique records are saved to Cosmos DB |
| Database accuracy & efficiency | Hash-indexed Cosmos DB ensures fast lookups |

## Architecture

```
User (Browser) → Azure App Service (Flask) → Azure Cosmos DB
                          ↓
                SHA-256 Hash Generation
                          ↓
                Duplicate Check Query
                          ↓
             UNIQUE → Save  |  DUPLICATE → Reject
```

## Technologies Used

- **Backend:** Python 3.11, Flask 3.0
- **Database:** Azure Cosmos DB for NoSQL (Free Tier)
- **Hosting:** Azure App Service (F1 Free Tier)
- **Hashing:** SHA-256 (hashlib)
- **Frontend:** HTML5, CSS3, Vanilla JavaScript

## How to Run Locally

```bash
git clone https://github.com/yourusername/CodeAlpha_DataRedundancy.git
cd CodeAlpha_DataRedundancy
pip install -r requirements.txt
```

Create a `.env` file:
```
COSMOS_ENDPOINT=https://your-account.documents.azure.com:443/
COSMOS_KEY=your_primary_key
COSMOS_DATABASE=RedundancyDB
COSMOS_CONTAINER=Records
```

```bash
python app.py
```

Open `http://localhost:5000` in your browser.

## Project Structure

```
CodeAlpha_DataRedundancy/
├── app.py
├── requirements.txt
├── .gitignore
├── README.md
└── templates/
    └── index.html
```

## How Duplicate Detection Works

1. User submits data via the web form
2. System normalizes data (lowercase, trim whitespace)
3. SHA-256 hash is generated from normalized data
4. Hash is queried against Azure Cosmos DB
5. If hash exists → **REDUNDANT** (rejected)
6. If hash is new → **UNIQUE** (saved to database)

## Author

**[Your Name]**
- LinkedIn: [Your LinkedIn URL]
- GitHub: [Your GitHub URL]

---
*CodeAlpha Cloud Computing Internship | Task 1*
