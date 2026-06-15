# FINTRACK — Financial Management System for Auto Shops

A full-stack web application for managing finances, service orders, parts catalog,
and WhatsApp CRM for automotive workshops.

![Python](https://img.shields.io/badge/Python-3.10-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.x-red)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14-blue)
![Java](https://img.shields.io/badge/Java-Spring%20Boot%203.2-green)

---

## About

FINTRACK is a web-based financial management system built for auto shops.
It allows managers to import service order reports from PDF, track monthly revenue,
set financial goals, manage a parts catalog for basic maintenance kits,
and send personalized WhatsApp messages to clients through a Java-powered CRM module.

---

## Features

- **Dashboard** — Monthly revenue chart, total service orders, goal tracking
- **PDF Import** — Upload service order reports; the system extracts and stores each OS automatically using regex parsing
- **Kit Revisão (Parts Catalog)** — Search by vehicle (model/motor) and get specific part references per manufacturer (e.g., Wega ML-100, Bosch 0986B00044, Tecfil PSL96)
- **CRM WhatsApp** — Import client list from Excel or XML, personalize messages with `[nome]`, `[veiculo]`, `[placa]` placeholders, and send via WhatsApp Web with one click
- **Role-based access** — Admin and manager profiles with different permissions
- **Duplicate prevention** — `ON CONFLICT` SQL prevents importing the same service order twice

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Python + Streamlit |
| Database | PostgreSQL |
| DB Driver | psycopg2 |
| Authentication | streamlit-authenticator (bcrypt) |
| PDF Parsing | pdfplumber + regex |
| Environment | python-dotenv |
| CRM Service | Java Spring Boot 3.2.5 |
| CRM Templates | Thymeleaf |
| Excel/XML Parsing | Apache POI 5.2.5 |

---

## Project Structure

```
FINTRACK-SYSTEM/
├── app.py                          # Main Streamlit app — routing and screens
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment variables template
│
├── config/
│   ├── database.py                 # PostgreSQL connection + table creation
│   └── security.py                 # Auth helpers
│
├── modules/
│   ├── leitor_pdf.py               # PDF parser for service order reports
│   ├── dashboard.py                # Revenue charts and metrics
│   ├── revisao.py                  # Parts catalog and vehicle registration
│   └── auth.py                     # Authentication module
│
├── assets/
│   └── style.css                   # Custom CSS
│
└── crm-java/                       # Standalone Java CRM module (port 8080)
    ├── pom.xml
    └── src/main/
        ├── java/com/fintrack/crm/
        │   ├── CrmController.java
        │   ├── ExcelParserService.java
        │   └── XmlParserService.java
        └── resources/
            └── templates/
                ├── crm-index.html
                └── crm-envio.html
```

---

## Getting Started

### Prerequisites
- Python 3.10+
- PostgreSQL 14+
- Java 17+ and Maven (for the CRM module)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/AdrianLopez001/FINTRACK-SYSTEM.git
cd FINTRACK-SYSTEM

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate      # Linux/Mac
venv\Scripts\activate         # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your PostgreSQL credentials

# 5. Run the app
streamlit run app.py
```

The app will be available at `http://localhost:8501`

### Running the CRM Module (optional)

```bash
cd crm-java
mvn spring-boot:run
```

CRM will be available at `http://localhost:8080/crm`

---

## Database

Tables are created automatically on first run:

- **`faturamento`** — Service orders imported from PDF (date, OS number, value)
- **`veiculos`** — Vehicle registry by license plate (brand, model, year, engine)
- **`kit_revisao_catalogo`** — Parts catalog indexed by vehicle model, year range, and engine type

---

## How PDF Parsing Works

The system reads the auto shop's service order report PDF using `pdfplumber`.
For each line that matches the OS pattern (`counter + OS_number + date`), it:

1. Extracts the **finalization date** (2nd date in the line = "Finalizada em")
2. Captures the **last monetary value** in the line (= total OS value in BRL format)
3. Uses `"OS {number}"` as a unique key to prevent duplicate imports via `ON CONFLICT`

---

## Screenshots

> Screenshots coming soon.

---

## License

MIT — free to use and modify.