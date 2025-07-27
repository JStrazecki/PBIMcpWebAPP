"""
Power BI utilities and helper functions
"""

from typing import Dict, Any, Optional, List
from ..config.constants import FINANCIAL_MEASURES, NATURAL_LANGUAGE_MAPPINGS
from ..config.dynamic_measures import dynamic_measure_manager
from ..utils.exceptions import MeasureNotFoundError


def get_measure_by_alias(alias: str) -> Optional[Dict[str, Any]]:
    """Find measure by name or alias"""
    alias_lower = alias.lower()
    
    # Check direct measure names
    if alias_lower in FINANCIAL_MEASURES:
        return FINANCIAL_MEASURES[alias_lower]
    
    # Check aliases
    for measure_key, measure_info in FINANCIAL_MEASURES.items():
        if "aliases" in measure_info:
            if alias_lower in [a.lower() for a in measure_info["aliases"]]:
                return measure_info
    
    # Check natural language mappings
    for nl_term, mapped_value in NATURAL_LANGUAGE_MAPPINGS.items():
        if nl_term in alias_lower:
            return mapped_value
    
    return None


def validate_measure_exists(measure_name: str) -> Dict[str, Any]:
    """Validate that a measure exists and return its definition using dynamic discovery"""
    # First try static mappings for backward compatibility
    measure_info = get_measure_by_alias(measure_name)
    if measure_info:
        return measure_info
    
    # Try dynamic measure manager
    actual_measure_name = dynamic_measure_manager.get_measure_mapping(measure_name)
    if actual_measure_name:
        # Build measure info for discovered measure
        discovered_measures = dynamic_measure_manager.get_all_discovered_measures()
        if actual_measure_name in [m.name for m in discovered_measures.values()]:
            return {
                'description': f"Discovered measure: {actual_measure_name}",
                'dax': f"[{actual_measure_name}]",
                'type': 'currency',  # Default type
                'name': actual_measure_name
            }
    
    # If not found anywhere, suggest available options
    static_available = list(FINANCIAL_MEASURES.keys())[:5]
    dynamic_mappings = list(dynamic_measure_manager.get_all_mappings().keys())[:5]
    all_available = static_available + [m for m in dynamic_mappings if m not in static_available]
    
    raise MeasureNotFoundError(
        f"Measure '{measure_name}' not found. Available: {', '.join(all_available[:10])}..."
    )


def parse_dax_results(result: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Parse DAX query results into structured format"""
    try:
        tables = result.get("results", [{}])[0].get("tables", [{}])[0]
        rows = tables.get("rows", [])
        return rows
    except (IndexError, KeyError, TypeError):
        return []


def extract_table_columns_from_tmdl(content: str) -> List[str]:
    """Extract table names from TMDL content"""
    tables = []
    
    for line in content.split('\n'):
        line = line.strip()
        if line.startswith('table '):
            table_name = line.split(' ')[1].strip("'\"")
            tables.append(table_name)
    
    return tables


def extract_measures_from_tmdl(content: str) -> List[str]:
    """Extract measure names from TMDL content"""
    measures = []
    
    lines = content.split('\n')
    for i, line in enumerate(lines):
        line = line.strip()
        if line.startswith('measure '):
            try:
                measure_name = line.split(' ', 1)[1].split('=')[0].strip().strip("'\"")
                measures.append(measure_name)
            except IndexError:
                continue
    
    return measures


def build_dimension_mapping() -> Dict[str, tuple]:
    """Build mapping of dimension names to table and column"""
    return {
        "customer": ("Contacts", "Contact Name"),
        "costcenter": ("Cost Centers", "Cost Center Name"), 
        "account": ("Accounts", "Account Name"),
        "date": ("_Date", "Date"),
        "period": ("_Period", "Period")
    }


def validate_dimension(dimension: str) -> tuple:
    """Validate dimension name and return table/column mapping"""
    dimension_map = build_dimension_mapping()
    
    if dimension.lower() not in dimension_map:
        available = list(dimension_map.keys())
        raise ValueError(f"Invalid dimension. Choose from: {', '.join(available)}")
    
    return dimension_map[dimension.lower()]


def build_financial_summary_dax() -> str:
    """Build DAX query for financial summary without period filtering"""
    # Use discovered measures where available, fallback to static
    def get_measure_dax(generic_name: str) -> str:
        actual_name = dynamic_measure_manager.get_measure_mapping(generic_name)
        if actual_name:
            return f"[{actual_name}]"
        return FINANCIAL_MEASURES.get(generic_name, {}).get('dax', f"[{generic_name}]")
    
    return f"""
    EVALUATE
    RETURN ROW(
        "Revenue", {get_measure_dax('revenue')},
        "Gross Profit", {get_measure_dax('gross_profit')},
        "EBITDA", {get_measure_dax('ebitda')},
        "Net Profit", {get_measure_dax('net_profit')},
        "Cash", {get_measure_dax('cash')},
        "Working Capital", {get_measure_dax('working_capital')},
        "Total Assets", {get_measure_dax('total_assets')},
        "Equity", {get_measure_dax('equity')}
    )
    """


def build_revenue_analysis_dax(breakdown_by: str, top_n: int = 10) -> str:
    """Build DAX query for revenue analysis by dimension without period filtering"""
    table_name, column_name = validate_dimension(breakdown_by)
    
    # Get actual revenue measure name
    revenue_measure = dynamic_measure_manager.get_measure_mapping('revenue')
    if not revenue_measure:
        revenue_measure = FINANCIAL_MEASURES['revenue']['dax']
    else:
        revenue_measure = f"[{revenue_measure}]"
    
    return f"""
    EVALUATE
    TOPN(
        {top_n},
        SUMMARIZECOLUMNS(
            '{table_name}'[{column_name}],
            "Revenue", {revenue_measure}
        ),
        [Revenue], DESC
    )
    ORDER BY [Revenue] DESC
    """


def build_measure_query_dax(measure_info: Dict[str, Any], breakdown_by: Optional[str] = None, top_n: int = 20) -> str:
    """Build DAX query for specific measure analysis without period filtering"""
    if breakdown_by:
        table_name, column_name = validate_dimension(breakdown_by)
        
        return f"""
        EVALUATE
        TOPN(
            {top_n},
            SUMMARIZECOLUMNS(
                '{table_name}'[{column_name}],
                "Value", {measure_info['dax']}
            ),
            [Value], DESC
        )
        ORDER BY [Value] DESC
        """
    else:
        return f"""
        EVALUATE
        ROW(
            "Current", {measure_info['dax']},
            "Prior Year", CALCULATE({measure_info['dax']}, SAMEPERIODLASTYEAR('_Date'[Date])),
            "YTD", CALCULATE({measure_info['dax']}, DATESYTD('_Date'[Date]))
        )
        """