"""
Constants and defaults for Power BI MCP Finance Server
Enhanced with dynamic measure discovery capabilities
"""

from typing import Dict, Any, Optional


def get_dynamic_measure_dax(generic_name: str) -> str:
    """Get dynamic DAX measure name, falling back to static if not available"""
    try:
        from .dynamic_measures import dynamic_measure_manager
        actual_measure = dynamic_measure_manager.get_measure_mapping(generic_name)
        if actual_measure:
            return f"[{actual_measure}]"
    except ImportError:
        pass  # Fall back to static measures if dynamic system not available
    
    # Fallback to static definition
    return FINANCIAL_MEASURES.get(generic_name, {}).get('dax', f'[{generic_name}]')


# Financial Model Definitions
POHODA_TABLES = {
    "Journals": {
        "description": "Central fact table with all accounting transactions",
        "key_columns": ["Journal Id", "Date Accounting", "Account Id", "Contact Id", 
                       "Cost Center Id", "Amount", "Currency", "Scenario"]
    },
    "Accounts": {
        "description": "Chart of accounts with financial statement mapping",
        "key_columns": ["Account Id", "Account Code", "Account Name", "Account Map"]
    },
    "Mapping": {
        "description": "Financial statement hierarchy mapping - CRITICAL for financial analysis",
        "key_columns": ["Account Id", "Account Code", "Account Name", "lvl1", "lvl2", "lvl3", "lvl4"],
        "hierarchy_info": {
            "lvl1": "Top level - EBITDA or Below EBITDA classification",
            "lvl2": "Secondary classification - more detailed financial categories", 
            "lvl3": "Tertiary classification - specific line items",
            "lvl4": "Most detailed level - granular account classification"
        },
        "usage": "Essential for financial statement analysis, P&L categorization, and determining if accounts are revenue, costs, assets, liabilities etc."
    },
    "Contacts": {
        "description": "Customer and supplier master data",
        "key_columns": ["Contact Id", "Contact Name", "ID TAX", "ID BUSINESS", "ID VAT"]
    },
    "Cost Centers": {
        "description": "Department/project tracking",
        "key_columns": ["Cost Center Id", "Cost Center Name", "Cost Center Owner"]
    },
    "_Date": {
        "description": "Calendar dimension with fiscal year support",
        "key_columns": ["Date", "Year", "Month", "Quarter", "Fiscal Year"]
    },
    "_Period": {
        "description": "Time analysis periods",
        "values": ["MTD", "QTD", "YTD", "LTM", "WTD"]
    }
}

# Financial Measures
FINANCIAL_MEASURES = {
    # Income Statement Measures
    "revenue": {
        "dax": "[Revenue]",
        "description": "Total sales revenue",
        "type": "currency",
        "statement": "income",
        "aliases": ["sales", "turnover", "income"]
    },
    "revenue_py": {
        "dax": "[Rev PY]", 
        "description": "Revenue prior year same period",
        "type": "currency",
        "statement": "income"
    },
    "revenue_growth": {
        "dax": "[∆Rev PY%]",
        "description": "Revenue growth vs prior year %",
        "type": "percentage",
        "statement": "income"
    },
    "gross_profit": {
        "dax": "[Gross Profit]",
        "description": "Revenue minus cost of sales",
        "type": "currency",
        "statement": "income",
        "aliases": ["gp", "gross margin amount"]
    },
    "gross_profit_pct": {
        "dax": "[Gross Profit %]",
        "description": "Gross profit margin percentage",
        "type": "percentage",
        "statement": "income",
        "aliases": ["gp%", "gross margin"]
    },
    "ebitda": {
        "dax": "[EBITDA]",
        "description": "Earnings before interest, tax, depreciation, amortization",
        "type": "currency",
        "statement": "income",
        "aliases": ["earnings", "operating profit"]
    },
    "ebitda_pct": {
        "dax": "[EBITDA %]",
        "description": "EBITDA margin percentage",
        "type": "percentage",
        "statement": "income"
    },
    "net_profit": {
        "dax": "[Profit Net]",
        "description": "Net profit after all expenses",
        "type": "currency",
        "statement": "income",
        "aliases": ["net income", "bottom line"]
    },
    
    # Balance Sheet Measures
    "cash": {
        "dax": "[Cash]",
        "description": "Cash and cash equivalents",
        "type": "currency",
        "statement": "balance",
        "aliases": ["cash position", "liquidity"]
    },
    "working_capital": {
        "dax": "[Working Capital]",
        "description": "Current assets minus current liabilities",
        "type": "currency",
        "statement": "balance",
        "aliases": ["wc", "net working capital"]
    },
    "net_debt": {
        "dax": "[Net Debt]",
        "description": "Total debt minus cash",
        "type": "currency",
        "statement": "balance",
        "aliases": ["debt position", "leverage"]
    },
    "total_assets": {
        "dax": "[Total Assets]",
        "description": "Sum of all assets",
        "type": "currency",
        "statement": "balance"
    },
    "equity": {
        "dax": "[Equity]",
        "description": "Shareholders' equity",
        "type": "currency",
        "statement": "balance",
        "aliases": ["shareholders equity", "net worth"]
    },
    "fixed_assets": {
        "dax": "[Fixed Assets]",
        "description": "Property, plant, and equipment",
        "type": "currency",
        "statement": "balance",
        "aliases": ["ppe", "tangible assets"]
    },
    
    # Variance Measures
    "amount_py": {
        "dax": "[Amt PY]",
        "description": "Amount prior year",
        "type": "currency"
    },
    "delta_py": {
        "dax": "[∆Amt PY]",
        "description": "Change vs prior year amount",
        "type": "currency"
    },
    "delta_py_pct": {
        "dax": "[∆Amt PY%]",
        "description": "Change vs prior year percentage",
        "type": "percentage"
    },
    "budget": {
        "dax": "[Bdgt]",
        "description": "Budget amount",
        "type": "currency"
    },
    "delta_budget": {
        "dax": "[∆Bdgt]",
        "description": "Variance vs budget amount",
        "type": "currency"
    },
    "delta_budget_pct": {
        "dax": "[∆Bdgt%]",
        "description": "Variance vs budget percentage",
        "type": "percentage"
    },
    "forecast": {
        "dax": "[Fcst]",
        "description": "Forecast amount",
        "type": "currency"
    },
    
    # Other Key Measures
    "overhead": {
        "dax": "[Overhead]",
        "description": "Total overhead expenses",
        "type": "currency",
        "statement": "income"
    },
    "overhead_pct": {
        "dax": "[Overhead %]",
        "description": "Overhead as % of revenue",
        "type": "percentage",
        "statement": "income"
    }
}

# Account mapping categories
ACCOUNT_MAPS = {
    "revenue": ["Revenue", "Sales", "Income"],
    "cogs": ["Cost of Sales", "COGS", "Direct Costs"],
    "overhead": ["Operating Expenses", "SG&A", "Admin"],
    "assets": ["Current Assets", "Fixed Assets", "Other Assets"],
    "liabilities": ["Current Liabilities", "Long Term Debt", "Other Liabilities"],
    "equity": ["Share Capital", "Retained Earnings", "Other Equity"]
}

# Common scenarios
SCENARIOS = ["Actual", "Plan", "Projection", "Budget", "Forecast"]

# Natural language mappings
NATURAL_LANGUAGE_MAPPINGS = {
    "this month": "MTD",
    "this quarter": "QTD", 
    "this year": "YTD",
    "year to date": "YTD",
    "last twelve months": "LTM",
    "rolling year": "LTM",
    "vs last year": "∆Amt PY%",
    "vs budget": "∆Bdgt%",
    "compared to": "vs"
}

# Monitoring Thresholds
MONITORING_THRESHOLDS = {
    "min_conversations": 10,
    "retry_threshold": 1.5,
    "slow_response_ms": 3000,
    "confusion_threshold": 3,
    "token_waste_threshold": 500
}

# Performance Limits
PERFORMANCE_LIMITS = {
    "max_query_length": 10000,
    "max_results": 1000,
    "default_timeout_ms": 30000,
    "max_retry_attempts": 3
}