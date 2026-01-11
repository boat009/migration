# Business Logic Migration Validator

🏦 **เครื่องมือตรวจสอบการ Migration แบบ Business Logic สำหรับกรณีที่ Schema ไม่เหมือนกัน**

เหมาะสำหรับการตรวจสอบข้อมูลที่ migrate จาก DB2 ไป PostgreSQL โดยใช้ Business Logic แทนการเปรียบเทียบ schema ตรง ๆ เช่น:
- ✅ เลขที่สัญญา (Contract Number) ต้องตรงกัน
- ✅ จำนวนเงินคงเหลือ (Outstanding Balance) ต้องเท่ากัน  
- ✅ ข้อมูลลูกค้า (Customer Data) ต้องสอดคล้อง
- ✅ ยอดรวมต่าง ๆ (Aggregated Totals) ต้องถูกต้อง

## 🎯 คุณสมบัติหลัก

### 📋 Contract Validation
- ตรวจสอบ Contract Number ว่า migrate ครบถ้วน
- เปรียบเทียบ Outstanding Balance (ยอดคงเหลือ)
- ตรวจสอบ Contract Status ว่าถูกต้อง
- เปรียบเทียบวันที่สร้างสัญญา

### 👥 Customer Validation  
- ตรวจสอบข้อมูลลูกค้าว่าถูกต้องครบถ้วน
- เปรียบเทียบ Customer Name, ID, Phone, Email
- ตรวจสอบยอดหนี้รวมของลูกค้า

### 📊 Aggregate Validation
- ตรวจสอบยอดรวมเงินคงค้างทั้งระบบ
- เปรียบเทียบจำนวน Contract ทั้งหมด  
- ตรวจสอบยอดรวมการชำระเงิน

### ⚙️ Custom Business Rules
- กำหนดกฎการตรวจสอบเพิ่มเติมได้
- ตรวจสอบความสอดคล้องระหว่างตาราง
- Validate ข้อมูลตาม Business Logic

## 🚀 การใช้งาน

### 1. แก้ไข Database Configuration
แก้ไขไฟล์ `config.yaml`:

```yaml
db2:
  host: "your_db2_host"
  database: "YOUR_DB"
  user: "db2admin"
  password: "your_password"

postgresql:
  host: "your_pg_host"  
  database: "migrated_db"
  user: "postgres"
  password: "your_password"
```

### 2. แก้ไข Business Mapping
แก้ไขไฟล์ `business_mapping.yaml` ให้ตรงกับโครงสร้างฐานข้อมูลของคุณ:

```yaml
contract_validation:
  contract_summary:
    db2_query: |
      SELECT 
        CONTRACT_NO as contract_number,
        OUTSTANDING_BALANCE as balance,
        CONTRACT_STATUS as status
      FROM YOUR_SCHEMA.CONTRACTS
    
    postgresql_query: |
      SELECT 
        contract_id as contract_number,
        current_balance as balance, 
        status_code as status
      FROM public.loan_contracts
  
  # Field mapping
  db2_key_field: "contract_number"
  pg_key_field: "contract_number"
  db2_balance_field: "balance"
  pg_balance_field: "balance"
  balance_tolerance: 1.00  # ยอมให้ผิดพลาดได้ 1 บาท
```

### 3. รันการตรวจสอบ

#### ตรวจสอบทั้งหมด:
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

## 📊 ตัวอย่างรายงาน

### Console Output
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
```

### รายงานที่สร้าง
- `business_validation.html` - รายงาน HTML สวยงามพร้อมกราฟ
- `business_validation.xlsx` - รายงาน Excel แยกตาม Sheet
- `business_validation.json` - รายงาน JSON สำหรับ automation
- `business_migration_validation.log` - Log รายละเอียด

## 🔧 การปรับแต่ง Business Mapping

### Contract Validation
```yaml
contract_validation:
  # กำหนด SQL Query สำหรับแต่ละ Database
  contract_summary:
    db2_query: |
      SELECT CONTRACT_NO, OUTSTANDING_BALANCE, STATUS
      FROM SCHEMA1.CONTRACTS
    postgresql_query: |
      SELECT contract_id, current_balance, status_code  
      FROM public.loan_contracts
  
  # กำหนด Field Mapping
  db2_balance_field: "OUTSTANDING_BALANCE"
  pg_balance_field: "current_balance"
  balance_tolerance: 1.00  # ยอมให้ผิดพลาดได้
```

### Status Code Mapping
```yaml
status_mapping:
  db2_to_postgresql:
    'ACTIVE': 'A'
    'CLOSED': 'C'
    'CANCELLED': 'X'
```

### Custom Validation Rules
```yaml
custom_rules:
  contract_balance_consistency:
    type: "sum_match"
    db2_query: |
      SELECT OUTSTANDING_BALANCE FROM SCHEMA1.CONTRACTS
    postgresql_query: |
      SELECT current_balance FROM public.loan_contracts
    tolerance: 100.00
```

## 💡 Best Practices

### 1. เริ่มต้นด้วย Sample Data
```bash
# ทดสอบกับข้อมูลส่วนเล็ก ๆ ก่อน
# แก้ไข SQL Query ให้ใส่ LIMIT หรือ WHERE condition
```

### 2. กำหนด Tolerance ที่เหมาะสม
```yaml
balance_tolerance: 1.00    # สำหรับเงิน (บาท)
percentage_tolerance: 0.01 # สำหรับเปอร์เซ็นต์
```

### 3. ใช้ Verbose Mode เพื่อ Debug
```bash
python business_migration_validator.py --config config.yaml --mapping business_mapping.yaml --verbose
```

### 4. ตรวจสอบทีละส่วน
```bash
# ตรวจสอบ Contract ก่อน
python business_migration_validator.py --contracts-only

# ถ้า Contract ผ่านแล้ว ค่อยตรวจสอบส่วนอื่น
python business_migration_validator.py --aggregates-only
```

## 🔍 การแก้ไขปัญหา

### ปัญหา SQL Query
1. ตรวจสอบชื่อ Schema, Table, Column ให้ถูกต้อง
2. ทดสอบ Query ใน Database โดยตรงก่อน
3. ใช้ `--verbose` เพื่อดู Query ที่รัน

### ปัญหา Balance ไม่ตรง
1. ตรวจสอบ Data Type (DECIMAL vs NUMERIC)
2. ปรับ `balance_tolerance` ให้เหมาะสม
3. ตรวจสอบการคำนวณ Interest, Fees

### ปัญหา Performance
1. เพิ่ม WHERE condition ใน SQL เพื่อลด Record
2. ใส่ Index ในฐานข้อมูล
3. รันแยกเป็นช่วงเวลา

## 📁 โครงสร้างไฟล์

```
migration/
├── business_migration_validator.py  # Main script สำหรับ business logic
├── business_logic_validator.py      # Core business validation logic  
├── business_mapping.yaml           # การกำหนด mapping และ rules
├── config.yaml                     # Database configuration
├── db_connection.py                # Database utilities
├── report_generator.py             # Report generation  
├── requirements.txt                # Dependencies
├── README_BUSINESS.md              # คู่มือนี้
└── reports/                        # รายงานที่สร้าง
    ├── business_validation.html
    ├── business_validation.xlsx
    └── business_validation.json
```

## 🎯 Use Cases

### 1. ธนาคาร/สถาบันการเงิน
- ตรวจสอบข้อมูลสินเชื่อ (Loan Data)
- ยอดคงเหลือลูกค้า (Customer Balance)
- การชำระเงิน (Payment Records)

### 2. บริษัทประกันภัย  
- ข้อมูลกรมธรรม์ (Policy Data)
- เบี้ยประกันค้างชำระ (Outstanding Premium)
- การเคลม (Claim Records)

### 3. ระบบ ERP
- ข้อมูลลูกค้า/ผู้จัดจำหน่าย
- ยอดขาย/ยอดซื้อ
- คงเหลือสินค้า (Inventory)

เครื่องมือนี้ยืดหยุ่นและปรับแต่งได้ตามความต้องการของธุรกิจ โดยเน้นการตรวจสอบความถูกต้องของข้อมูลสำคัญที่ส่งผลต่อการดำเนินธุรกิจ 🏆