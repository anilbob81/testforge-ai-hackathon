# Test Data Requirements
# Used by the test-data-validator skill
# Complete reference of all data required by the test suite

---

## Environment Configuration

| Setting | Value | File |
|---------|-------|------|
| Maximo Base URL | https://nexersno.manage.nexersno.apps.demo1.nexersaas.com/maximo | config/agent_config.py |
| API Endpoint | https://nexersno-all.manage.nexersno.apps.demo1.nexersaas.com/maximo/api | config/agent_config.py |
| Site ID | BEDFORD | config/agent_config.py |
| Organization | EAGLENA | config/agent_config.py |

---

## P2P Workflow Data Requirements

All of the following must exist and be in the correct state before running `pr_to_po`.

### Vendor (Required for PR and PO creation)
| Field | Required Value | Maximo Path |
|-------|---------------|-------------|
| Vendor Number | EMI | Purchasing → Companies |
| Status | ACTIVE | Company record status field |
| Organization | EAGLENA | Company → Organizations tab |
| Purchasing enabled | Yes | Company → Purchasing tab |

### Site and Organization
| Field | Required Value |
|-------|---------------|
| Site ID | BEDFORD |
| Organization | EAGLENA |
| Currency | USD (or local currency configured) |

### Storeroom (Required for Receipt creation)
| Field | Required Value | Maximo Path |
|-------|---------------|-------------|
| Storeroom ID | CENTRAL | Inventory → Storerooms |
| Status | ACTIVE | Storeroom status field |
| Site | BEDFORD | Storeroom site field |
| Organization | EAGLENA | Storeroom org field |

**Note (MAS 9.2)**: Storeroom must be ACTIVE status. MAS 9.2 no longer accepts
storerooms in any status — it enforces ACTIVE explicitly.

### Item (Required for PO line items)
| Field | Required Value | Maximo Path |
|-------|---------------|-------------|
| Item Number | TEST-ITEM-001 | Inventory → Item Master |
| Description | Test Item for Automation | Item description field |
| Commodity | PARTS | Commodity field |
| Status | ACTIVE | Item status |

### GL Account (Required for PO and Invoice)
| Field | Required Value |
|-------|---------------|
| GL Account format | Must match org's configured format |
| Default account | Must exist in Maximo chart of accounts |

---

## Work Order Data Requirements

| Required Data | Value | Notes |
|--------------|-------|-------|
| Site | BEDFORD | Must exist |
| Asset type | Not required (WO can be unlinked from asset) |
| Location | Any active location in BEDFORD site |
| Craft | Any active craft in BEDFORD |

---

## PM Maintenance Data Requirements

| Required Data | Value | Notes |
|--------------|-------|-------|
| Site | BEDFORD | Must exist |
| Asset | Any active asset in BEDFORD | PM must be linked |
| Frequency unit | Days, Weeks, or Months | Configured in PM record |
| Job Plan | Any active Job Plan | For wo_from_jobplan workflow |

---

## Asset Management Data Requirements

| Required Data | Value | Notes |
|--------------|-------|-------|
| Site | BEDFORD | Must exist |
| Location | CENTRAL-BLDG (or any valid location) | Must be OPERATING status |
| Asset class | Not required | Optional classification |

---

## Data Validation Queries (for MCP tool use)

### Check Vendor
```
objectStructure: mxvendor
where: vendornum="EMI" and orgid="EAGLENA"
select: vendornum,status,name
```

### Check Storeroom
```
objectStructure: mxinvbalances
where: storeloc="CENTRAL" and siteid="BEDFORD"
select: storeloc,status,siteid,orgid
```

### Check Site
```
objectStructure: mxsite
where: siteid="BEDFORD"
select: siteid,description,status
```

### Check Item
```
objectStructure: mxitem
where: itemnum="TEST-ITEM-001"
select: itemnum,description,status
```

---

## Quick Fix Commands (Maximo Admin Navigation)

| Problem | Maximo Navigation Path |
|---------|----------------------|
| Vendor inactive | Purchasing → Companies → search EMI → Change Status → ACTIVE |
| Storeroom inactive | Inventory → Storerooms → search CENTRAL → Change Status → ACTIVE |
| Item missing | Inventory → Item Master → New Item → fill fields → Save |
| Site inactive | System Config → Platform Config → Sites → search BEDFORD |
| Org inactive | System Config → Platform Config → Organizations → EAGLENA |

---

## GO / NO-GO Decision

| Scenario | Decision |
|----------|----------|
| All data active and correctly configured | GO — run tests |
| 1 item inactive but fixable in < 5 min | FIX first, then GO |
| Multiple items inactive | NO-GO — fix environment first |
| Data missing (not just inactive) | NO-GO — data creation required |
| Site or Org missing | ESCALATE — system-level configuration needed |
