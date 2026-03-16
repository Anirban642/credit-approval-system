# Credit Approval System

A Django REST Framework based credit approval system.

## Tech Stack
- Django 4+
- Django REST Framework
- PostgreSQL
- Celery + Redis
- Docker

## Setup & Run

### Prerequisites
- Docker Desktop installed and running

### Run the application
```bash
docker compose up --build
```

The server will start at http://localhost:8000

## API Endpoints

### Register Customer
POST /register/
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "age": 30,
  "monthly_income": 50000,
  "phone_number": 9876543210
}
```

### Check Loan Eligibility
POST /check-eligibility/
```json
{
  "customer_id": 1,
  "loan_amount": 100000,
  "interest_rate": 15,
  "tenure": 12
}
```

### Create Loan
POST /create-loan/
```json
{
  "customer_id": 1,
  "loan_amount": 100000,
  "interest_rate": 15,
  "tenure": 12
}
```

### View Loan
GET /view-loan/{loan_id}/

### View All Loans by Customer
GET /view-loans/{customer_id}/

## Data Ingestion
Customer and loan data is automatically ingested from xlsx files on startup.