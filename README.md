# Credit Service API

Backend service for managing user credits, payments, and financial planning.

The system provides tools for tracking credit activity, analyzing performance, and importing plan data from Excel files.

---

## 🚀 Key Features

- **User Credit Overview**  
  Retrieve detailed information about user credits, including status (open/closed), payments, and overdue days.

- **Plan Import via Excel**  
  Upload monthly financial plans with validation (date format, category existence, uniqueness).

- **Performance Analytics**  
  Compare planned vs actual values for a selected period.

- **Yearly Statistics**  
  Monthly breakdown with performance percentages and contribution to yearly totals.

- **Database Seeding**  
  Load test data from CSV files for quick setup.

---

## 🛠 Tech Stack

- FastAPI  
- SQLAlchemy (async)  
- PostgreSQL  
- Alembic  
- Docker & Docker Compose  
- Pandas  

---

## ⚙️ How to Run

### 1. Configure environment

Create `.env` file:

```bash
cp .env.example .env
```

### 2. Start the project

🚀 **Run the project with Docker**

```bash
docker-compose up --build
```
### 3. Automated workflow

The entrypoint script handles the following automatically on container startup:

- Database readiness: Waits for PostgreSQL to be available
- Migrations: Runs alembic upgrade head to ensure the schema is up-to-date
- Data seeding: Populates the database with initial CSV data (users, credits, payments, plans) if not already present


### 4. Manual commands (optional)

If you need to re-run migrations or seed data while the container is running:
```bash
# Run migrations manually
docker-compose exec credit_service alembic upgrade head

# Run seeding manually
docker-compose exec credit_service python -m app.seed
```
### 📄 API Documentation

Once the service is running, the interactive **Swagger UI** is available at:

👉 [http://localhost:8000/docs](http://localhost:8000/docs)

### 📂 Project Structure

```
├── app/                   # Main application package
│   ├── __init__.py
│   ├── crud.py            # Data access layer (CRUD operations)
│   ├── database.py        # Database connection & session management
│   ├── exceptions.py      # Custom business exceptions
│   ├── main.py            # FastAPI app initialization & entry point
│   ├── models.py          # SQLAlchemy ORM models
│   ├── routers.py         # API endpoints & routing logic
│   ├── schemas.py         # Pydantic schemas (data validation)
│   ├── seed.py            # ETL logic for initial DB population
│   └── services.py        # Business logic & analytical reports
├── data/                  # Source data for seeding
│   ├── credits.csv
│   ├── dictionary.csv
│   ├── payments.csv
│   ├── plans.csv
│   └── users.csv
├── migrations/            # Alembic migration environment
│   ├── versions/          # Version-controlled schema changes
│   ├── env.py
│   ├── README
│   └── script.py.mako
├── alembic.ini            # Alembic configuration file
├── docker-compose.yml     # Service orchestration (App + DB)
├── Dockerfile             # Container definition
├── entrypoint.sh          # Automation script (Wait for DB -> Migrate -> Seed)
├── requirements.txt       # Project dependencies
├── .example.env           # Environment configuration template
└── .gitignore             # Git ignore rules
```
## API Demonstration (Swagger UI)
### 💳 1. Credits API Endpoints

- **GET /credits/user_credits/{user_id}**  
  Retrieve all credits for a specific user, including status (open/closed), payments, and overdue days.

- **POST /credits/plans_insert**  
  Upload monthly financial plans via Excel/CSV with validation (date format, category existence, uniqueness).

- **GET /credits/plans_performance**  
  Compare planned vs actual values for a selected period to analyze performance.

- **GET /credits/year_performance**  
  Get a monthly breakdown of credit performance with percentages and contribution to yearly totals.

<img width="1151" height="344" alt="зображення" src="https://github.com/user-attachments/assets/a31513de-7f8f-44a1-88d0-95fe9ef73b6e" />


### 2. Get User Credits

This endpoint retrieves all credit information for a specific user by their ID.  
It shows both closed and active credits, overdue days, and payment breakdowns.
<img width="1162" height="857" alt="зображення" src="https://github.com/user-attachments/assets/0750a11c-a55a-4f6a-8a3a-60fd2b8c6ac6" />

### 3. Upload Credit Plans

This endpoint (`POST /credits/plans_insert`) is used to upload credit issuance and collection plans into the system.  
It accepts an Excel file (`.xlsx`) via `multipart/form-data` and stores the validated data in the database.  
Useful for bulk data entry and financial planning automation.

<img width="1152" height="843" alt="зображення" src="https://github.com/user-attachments/assets/33fee7ed-8c8a-4847-8f5a-3292abe4cede" />

### 4. Plans Performance

This endpoint (`GET /credits/plans_performance`) returns performance data comparing **planned vs actual** credit issuance and collection for a given date.  
<img width="1146" height="774" alt="зображення" src="https://github.com/user-attachments/assets/5b6e3853-63e9-45ea-87d2-5823fc1bacdf" />

### 5. Year Performance

This endpoint (`GET /credits/year_performance`) provides a **yearly performance overview** of credit issuance and payments.  
It requires a parameter `year` (integer), which specifies the year for analysis.  
ends and comparing monthly performance within a given year.
<img width="1011" height="824" alt="зображення" src="https://github.com/user-attachments/assets/a0286b2b-ab49-438f-aa11-12ff98012754" />



