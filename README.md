# DB2 to PostgreSQL Migration Validation Tool

เครื่องมือตรวจสอบการ Migration จาก IBM DB2 ไป PostgreSQL ที่ครอบคลุมและอัตโนมัติ

## คุณสมบัติ

### 🔍 Schema Validation
- เปรียบเทียบ Tables, Columns, Data Types
- ตรวจสอบ Primary Keys และ Indexes
- รายงานความแตกต่างของโครงสร้างฐานข้อมูล

### 📊 Data Validation
- เปรียบเทียบจำนวน Records
- ตรวจสอบ Data Integrity ด้วย Checksum
- Validate Data Types และ Constraints
- ตรวจสอบ Primary Key Consistency

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

## ตัวอย่างรายงาน

### Console Output
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

### รายงานที่สร้าง
- `migration_validation_YYYYMMDD_HHMMSS.html` - รายงาน HTML แบบ Interactive
- `migration_validation_YYYYMMDD_HHMMSS.xlsx` - รายงาน Excel หลาย Sheets
- `migration_validation_YYYYMMDD_HHMMSS.json` - รายงาน JSON สำหรับ Automation
- `migration_validation.log` - Log File รายละเอียด

## โครงสร้างโปรแกรม

```
migration/
├── migration_validator.py    # Main script
├── db_connection.py         # Database connection utilities
├── schema_validator.py      # Schema comparison logic
├── data_validator.py        # Data validation logic
├── report_generator.py      # Report generation
├── config.yaml             # Configuration file
├── requirements.txt        # Python dependencies
├── README.md              # Documentation
└── reports/               # Generated reports directory
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

## คำแนะนำ Best Practices

1. **ทดสอบ Connection ก่อน**: ใช้ `--schema-only` เพื่อทดสอบการเชื่อมต่อ
2. **Validate Schema ก่อน Data**: แก้ไขปัญหา Schema ก่อนตรวจสอบ Data
3. **ใช้ Sample Tables**: ทดสอบกับ Tables เล็ก ๆ ก่อน
4. **Backup Configuration**: สำรองไฟล์ config.yaml
5. **Monitor Resources**: ตรวจสอบ CPU/Memory ระหว่างการ validate

## License

MIT License - ใช้งานและแก้ไขได้อย่างอิสระ