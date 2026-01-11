# DB2 to PostgreSQL Migration Validation Tool

เครื่องมือตรวจสอบการ Migration จาก IBM DB2 ไป PostgreSQL ที่ครอบคลุมและอัตโนมัติ

มี 2 โหมดการใช้งาน:
1. **Schema Validation** - เปรียบเทียบ schema ตรง ๆ (สำหรับกรณีที่โครงสร้างเหมือนกัน)
2. **Business Logic Validation** - ตรวจสอบตาม business logic (สำหรับกรณีที่ schema ไม่เหมือนกัน) 🆕

## 🎯 คุณสมบัติ

### 🔍 Schema Validation (โหมดมาตรฐาน)
- เปรียบเทียบ Tables, Columns, Data Types
- ตรวจสอบ Primary Keys และ Indexes
- รายงานความแตกต่างของโครงสร้างฐานข้อมูล

### 📊 Data Validation (โหมดมาตรฐาน)
- เปรียบเทียบจำนวน Records
- ตรวจสอบ Data Integrity ด้วย Checksum
- Validate Data Types และ Constraints
- ตรวจสอบ Primary Key Consistency

### 🏦 Business Logic Validation (โหมดใหม่) 🆕
- ✅ ตรวจสอบ Contract Numbers ว่า migrate ครบถ้วน
- ✅ เปรียบเทียบจำนวนเงินคงเหลือ (Outstanding Balance)
- ✅ ตรวจสอบข้อมูลลูกค้า (Customer Data)
- ✅ เปรียบเทียบยอดรวมต่าง ๆ (Aggregated Totals)
- ✅ Custom Business Rules ตามความต้องการ
- ✅ รองรับ Table/Column ที่ชื่อต่างกัน
- ✅ Flexible Field Mapping System

### 📋 Comprehensive Reporting
- รายงานแบบ Console (สีสัน)
- รายงานแบบ HTML (Interactive)
- รายงานแบบ Excel (Multiple Sheets)
- รายงานแบบ JSON (Machine Readable)

## การติดตั้ง

### 1. ติดตั้ง Dependencies
```bash
pip install -r requirements.txt
```

### 2. ติดตั้ง Database Drivers

#### สำหรับ DB2:
```bash
# Windows
pip install ibm_db

# หรือ download IBM Data Server Driver Package
# https://www.ibm.com/support/pages/download-initial-version-115-clients-and-drivers
```

#### สำหรับ PostgreSQL:
```bash
pip install psycopg2-binary
```

## การใช้งาน

### 1. แก้ไข Configuration
แก้ไขไฟล์ `config.yaml`:

```yaml
db2:
  host: "your_db2_host"
  port: 50000
  database: "YOUR_DB"
  user: "your_user"
  password: "your_password"

postgresql:
  host: "your_pg_host"
  port: 5432
  database: "migrated_db"
  user: "postgres"
  password: "your_password"

validation:
  db2_schema: "YOUR_SCHEMA"
  postgresql_schema: "public"
```

### 2. รันการตรวจสอบ

## 📋 Schema Validation (โหมดมาตรฐาน)
สำหรับกรณีที่โครงสร้าง schema เหมือนกัน

#### ตรวจสอบทั้งหมด (Schema + Data):
```bash
python migration_validator.py --config config.yaml
```

#### ตรวจสอบเฉพาะ Schema:
```bash
python migration_validator.py --config config.yaml --schema-only
```

#### ตรวจสอบเฉพาะ Data:
```bash
python migration_validator.py --config config.yaml --data-only
```

#### ตรวจสอบ Tables เฉพาะ:
```bash
python migration_validator.py --config config.yaml --data-only --tables TABLE1 TABLE2
```

#### เปิด Verbose Logging:
```bash
python migration_validator.py --config config.yaml --verbose
```

## 🏦 Business Logic Validation (โหมดใหม่) 🆕
สำหรับกรณีที่ schema ไม่เหมือนกัน แต่ต้องการตรวจสอบ business logic

### 1. แก้ไข Business Mapping
แก้ไขไฟล์ `business_mapping.yaml` ให้ตรงกับโครงสร้างของคุณ:

```yaml
contract_validation:
  contract_summary:
    db2_query: |
      SELECT CONTRACT_NO, OUTSTANDING_BALANCE, CONTRACT_STATUS
      FROM YOUR_SCHEMA.CONTRACTS
    postgresql_query: |
      SELECT contract_id, current_balance, status_code
      FROM public.loan_contracts
  
  db2_balance_field: "OUTSTANDING_BALANCE"
  pg_balance_field: "current_balance"
  balance_tolerance: 1.00  # ยอมให้ผิดพลาดได้ 1 บาท
```

### 2. รันการตรวจสอบ Business Logic

#### ตรวจสอบทั้งหมด (Contract + Customer + Aggregates + Custom Rules):
```bash
python business_migration_validator.py --config config.yaml --mapping business_mapping.yaml
```

#### ตรวจสอบเฉพาะ Contract:
```bash
python business_migration_validator.py --config config.yaml --mapping business_mapping.yaml --contracts-only
```

#### ตรวจสอบเฉพาะลูกค้า:
```bash
python business_migration_validator.py --config config.yaml --mapping business_mapping.yaml --customers-only
```

#### ตรวจสอบยอดรวม:
```bash
python business_migration_validator.py --config config.yaml --mapping business_mapping.yaml --aggregates-only
```

#### ตรวจสอบกฎที่กำหนดเอง:
```bash
python business_migration_validator.py --config config.yaml --mapping business_mapping.yaml --custom-only
```

#### เปิด Verbose Mode:
```bash
python business_migration_validator.py --config config.yaml --mapping business_mapping.yaml --verbose
```

## ตัวอย่างรายงาน

### Schema Validation Report
```
================================================================================
DB2 TO POSTGRESQL MIGRATION VALIDATION REPORT
Generated: 2024-01-15 14:30:25
================================================================================

SCHEMA VALIDATION SUMMARY
----------------------------------------
Tables Migrated: 25
Tables Missing: 2
Tables with Schema Issues: 3

SCHEMA DIFFERENCES
----------------------------------------
Table: CUSTOMERS
  Type Mismatch: CUSTOMER_ID (DB2: INTEGER, PG: bigint)
  Missing Column: CREATED_DATE

DATA VALIDATION SUMMARY
----------------------------------------
Total Tables Validated: 25
Row Count Matches: 23
Checksum Matches: 20
Primary Key Matches: 25
Overall Success Rate: 92.0%
```

### Business Logic Validation Report 🆕
```
================================================================================
BUSINESS LOGIC MIGRATION VALIDATION REPORT
Generated: 2024-01-15 14:30:25
================================================================================

OVERALL SUMMARY
----------------------------------------
Total Validations: 8
Passed Validations: 7
Overall Success Rate: 87.5%
Validation Status: FAILED

CONTRACT VALIDATION
----------------------------------------
Total Contracts Compared: 1,250
Perfect Matches: 1,245
Success Rate: 99.6%
Migration Completeness: 100.0%

Balance Mismatches (3):
  Contract CT001234: DB2=50000.00, PG=49999.50
  Contract CT001567: DB2=75000.00, PG=75000.25

AGGREGATE VALIDATION
----------------------------------------
total_outstanding_balance: PASS
  DB2: 15,750,000.00, PG: 15,749,998.75, Diff: 1.25
active_contract_count: PASS
  DB2: 1250, PG: 1250, Diff: 0

CUSTOM BUSINESS RULES
----------------------------------------
customers_with_contracts: PASS
total_interest_outstanding: PASS
current_month_payments: FAIL
```

### รายงานที่สร้าง

#### Schema Validation Reports:
- `migration_validation_YYYYMMDD_HHMMSS.html` - รายงาน HTML แบบ Interactive
- `migration_validation_YYYYMMDD_HHMMSS.xlsx` - รายงาน Excel หลาย Sheets
- `migration_validation_YYYYMMDD_HHMMSS.json` - รายงาน JSON สำหรับ Automation
- `migration_validation.log` - Log File รายละเอียด

#### Business Logic Validation Reports: 🆕
- `business_validation.html` - รายงาน HTML สวยงามพร้อมกราฟและสี
- `business_validation.xlsx` - รายงาน Excel แยกตาม Sheet (Summary, Contract Issues, Customer Issues)
- `business_validation.json` - รายงาน JSON สำหรับ automation และ integration
- `business_migration_validation.log` - Log File รายละเอียดสำหรับ business logic

## โครงสร้างโปรแกรม

```
migration/
├── migration_validator.py           # Main script (Schema validation)
├── business_migration_validator.py  # Main script (Business logic validation) 🆕
├── db_connection.py                 # Database connection utilities
├── schema_validator.py              # Schema comparison logic
├── data_validator.py                # Data validation logic
├── business_logic_validator.py      # Business logic validation 🆕
├── report_generator.py              # Report generation
├── config.yaml                      # Database configuration
├── business_mapping.yaml            # Business logic mapping 🆕
├── requirements.txt                 # Python dependencies
├── README.md                        # Documentation (main)
├── README_BUSINESS.md               # Business logic documentation 🆕
└── reports/                         # Generated reports directory
    ├── migration_validation_*.html   # Schema validation reports
    ├── business_validation.html      # Business logic reports 🆕
    └── ...
```

## Configuration Options

### Database Settings
```yaml
db2:
  host: "hostname"
  port: 50000
  database: "database_name"
  user: "username"
  password: "password"

postgresql:
  host: "hostname"
  port: 5432
  database: "database_name"
  user: "username"
  password: "password"
```

### Validation Settings
```yaml
validation:
  db2_schema: "SCHEMA_NAME"           # DB2 schema to validate
  postgresql_schema: "public"         # Target PostgreSQL schema
  max_tables_to_validate: 50         # Limit for performance
```

### Output Settings
```yaml
output:
  directory: "./reports"              # Report output directory
  filename: "migration_validation"    # Base filename
  console: true                      # Show console output
```

## การแก้ไขปัญหา

### ปัญหาการเชื่อมต่อ DB2
1. ตรวจสอบ IBM Data Server Driver Package
2. ตรวจสอบ Network connectivity
3. ตรวจสอบ User privileges

### ปัญหาการเชื่อมต่อ PostgreSQL
1. ตรวจสอบ pg_hba.conf settings
2. ตรวจสอบ PostgreSQL service status
3. ตรวจสอบ Network firewall

### ปัญหา Performance
1. ใช้ `max_tables_to_validate` เพื่อจำกัดจำนวน tables
2. เพิ่ม `query_timeout` ใน advanced settings
3. รัน validation แยกเป็นส่วน ๆ

## 💡 คำแนะนำ Best Practices

### Schema Validation (โหมดมาตรฐาน)
1. **ทดสอบ Connection ก่อน**: ใช้ `--schema-only` เพื่อทดสอบการเชื่อมต่อ
2. **Validate Schema ก่อน Data**: แก้ไขปัญหา Schema ก่อนตรวจสอบ Data
3. **ใช้ Sample Tables**: ทดสอบกับ Tables เล็ก ๆ ก่อน
4. **Backup Configuration**: สำรองไฟล์ config.yaml
5. **Monitor Resources**: ตรวจสอบ CPU/Memory ระหว่างการ validate

### Business Logic Validation (โหมดใหม่) 🆕
1. **เริ่มต้นด้วย Contract Validation**: `--contracts-only` ก่อนตรวจสอบส่วนอื่น
2. **กำหนด Tolerance ที่เหมาะสม**: 
   ```yaml
   balance_tolerance: 1.00    # สำหรับเงิน (บาท)
   percentage_tolerance: 0.01 # สำหรับเปอร์เซ็นต์
   ```
3. **ทดสอบ SQL Query ก่อน**: รัน query ใน database โดยตรงให้ถูกต้องก่อน
4. **ใช้ Verbose Mode**: `--verbose` เพื่อดู query และ debug
5. **แบ่งการตรวจสอบ**: รันทีละส่วนแทนที่จะรันทั้งหมดพร้อมกัน

### เคล็ดลับสำหรับ Business Logic
- ✅ ตรวจสอบ Data Type mapping (INTEGER vs BIGINT, DECIMAL vs NUMERIC)
- ✅ ใส่ WHERE condition เพื่อลด record ในการทดสอบ
- ✅ สร้าง index ในฐานข้อมูลเพื่อเพิ่มความเร็ว
- ✅ กำหนด timeout ที่เหมาะสมใน config
- ✅ ใช้ connection pooling สำหรับ database ขนาดใหญ่

## 🎯 เลือกโหมดที่เหมาะสม

### ใช้ Schema Validation เมื่อ:
- โครงสร้าง schema เหมือนกัน (table และ column ชื่อเดียวกัน)
- ต้องการตรวจสอบ schema แบบรายละเอียด
- มีเวลาแก้ไข schema ให้ตรงกัน

### ใช้ Business Logic Validation เมื่อ: 🆕
- โครงสร้าง schema ไม่เหมือนกัน (table/column ชื่อต่างกัน)
- ต้องการตรวจสอบข้อมูลสำคัญ (เลขสัญญา, ยอดเงิน)
- ระบบเดิมและใหม่ออกแบบแตกต่างกัน
- **เหมาะกับงาน migration จริงมากที่สุด** 🎯

## 📚 เอกสารเพิ่มเติม

- **README_BUSINESS.md** - คู่มือ Business Logic Validation แบบละเอียด
- **business_mapping.yaml** - ตัวอย่างการกำหนด mapping และ rules
- **config.yaml** - ตัวอย่างการตั้งค่าฐานข้อมูล

## License

MIT License - ใช้งานและแก้ไขได้อย่างอิสระ