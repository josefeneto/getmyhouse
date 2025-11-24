"""
Report Agent - Specialist agent for generating property reports.

This agent formats property data into structured tables and generates
Excel exports for user download.

Based on Google ADK Day 1 concepts: Specialized agents with focused output generation.
"""

import logging
from typing import Any, Dict, List
from io import BytesIO

import pandas as pd
from google.adk.agents import LlmAgent

from src.config import ADKConfig, AgentConfig

# Configure logging
logger = logging.getLogger(__name__)


class ReportAgent:
    """
    Specialist agent for report generation.
    
    This agent:
    - Formats property data into structured tables
    - Generates summary statistics
    - Creates Excel exports
    - Includes verified property links
    """
    
    def __init__(self, model: str = ADKConfig.MODEL_NAME):
        """
        Initialize the report agent.
        
        Args:
            model: Name of the LLM model to use
        """
        self.model = model
        self._agent = self._create_agent()
        
        logger.info("Report agent initialized successfully")
    
    def _create_agent(self) -> LlmAgent:
        """
        Create the ADK LlmAgent instance.
        
        Returns:
            LlmAgent configured for report generation
        """
        agent = LlmAgent(
            name="property_report",
            model=self.model,
            instruction=AgentConfig.REPORT_AGENT_INSTRUCTION,
            # Note: Temperature controlled by model in ADK
        )
        
        return agent
    
    async def generate_report(
        self,
        properties: List[Dict[str, Any]],
        requirements: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive property report.
        
        Args:
            properties: List of filtered properties to report
            requirements: Original search requirements
            
        Returns:
            Dictionary containing:
            - table_data: List of property dictionaries formatted for display
            - summary: Dictionary with statistics
            - excel_data: BytesIO object with Excel export (optional)
        """
        logger.info(f"Generating report for {len(properties)} properties")
        
        if not properties:
            logger.warning("No properties to report")
            return {
                "table_data": [],
                "summary": {"total": 0},
                "excel_data": None,
            }
        
        try:
            # Format properties for display
            table_data = self._format_table_data(properties)
            
            # Generate summary statistics
            summary = self._generate_summary(properties, requirements)
            
            # Create Excel export
            excel_data = self._create_excel_export(table_data, summary)
            
            logger.info("Report generated successfully")
            
            return {
                "table_data": table_data,
                "summary": summary,
                "excel_data": excel_data,
            }
            
        except Exception as e:
            logger.error(f"Report generation failed: {str(e)}", exc_info=True)
            return {
                "table_data": [],
                "summary": {"error": str(e)},
                "excel_data": None,
            }
    
    def _format_table_data(
        self,
        properties: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Format property data for table display.
        
        Ensures consistent column structure with all required attributes.
        
        Args:
            properties: Raw property data
            
        Returns:
            List of formatted property dictionaries
        """
        formatted = []
        
        for idx, prop in enumerate(properties, 1):
            formatted_prop = {
                "Rank": idx,
                "Location": prop.get("location", "N/A"),
                "Type": prop.get("type", "N/A"),
                "Typology": prop.get("typology", "N/A"),
                "Price (EUR)": f"€{prop.get('price', 0):,}",
                "WCs": prop.get("wcs", "N/A"),
                "State": prop.get("state", "N/A"),
                "Transport (min)": prop.get("transport_distance", "N/A"),
                "Agency": prop.get("agency", "N/A"),
                "Match Score": f"{prop.get('match_score', 0):.0%}",
                "Link": prop.get("url", "N/A"),
            }
            formatted.append(formatted_prop)
        
        return formatted
    
    def _generate_summary(
        self,
        properties: List[Dict[str, Any]],
        requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate summary statistics for the report.
        
        Args:
            properties: List of properties
            requirements: Original search requirements
            
        Returns:
            Dictionary with summary statistics
        """
        if not properties:
            return {"total": 0}
        
        prices = [p.get("price", 0) for p in properties if p.get("price")]
        scores = [p.get("match_score", 0) for p in properties if p.get("match_score")]
        
        summary = {
            "total": len(properties),
            "search_country": requirements.get("country", "Portugal"),
            "search_location": requirements.get("location", "N/A"),
            "search_type": requirements.get("property_type", "N/A"),
            "price_range": {
                "min": f"€{min(prices):,}" if prices else "N/A",
                "max": f"€{max(prices):,}" if prices else "N/A",
                "avg": f"€{int(sum(prices) / len(prices)):,}" if prices else "N/A",
            },
            "match_score": {
                "avg": f"{sum(scores) / len(scores):.0%}" if scores else "N/A",
                "best": f"{max(scores):.0%}" if scores else "N/A",
            },
            "typologies": self._count_typologies(properties),
        }
        
        return summary
    
    def _count_typologies(
        self,
        properties: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """
        Count properties by typology.
        
        Args:
            properties: List of properties
            
        Returns:
            Dictionary mapping typology to count
        """
        counts = {}
        for prop in properties:
            typology = prop.get("typology", "Unknown")
            counts[typology] = counts.get(typology, 0) + 1
        
        return counts
    
    def _create_excel_export(
        self,
        table_data: List[Dict[str, Any]],
        summary: Dict[str, Any]
    ) -> BytesIO:
        """
        Create Excel export with property data and summary.
        
        Args:
            table_data: Formatted property data
            summary: Summary statistics
            
        Returns:
            BytesIO object containing Excel file
        """
        try:
            # Create Excel writer
            output = BytesIO()
            
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                # Properties sheet - convert display format to Excel-friendly format
                excel_data = []
                for row in table_data:
                    excel_row = {
                        "Rank": row["Rank"],
                        "Location": row["Location"],
                        "Type": row["Type"],
                        "Typology": row["Typology"],
                        "Price (EUR)": self._extract_price(row["Price (EUR)"]),
                        "WCs": row["WCs"],
                        "State": row["State"],
                        "Transport (min)": row["Transport (min)"],
                        "Agency": row["Agency"],
                        "Match Score": self._extract_percentage(row["Match Score"]),
                        "Link": row["Link"],
                    }
                    excel_data.append(excel_row)
                
                df_properties = pd.DataFrame(excel_data)
                df_properties.to_excel(
                    writer,
                    sheet_name='Properties',
                    index=False
                )
                
                # Summary sheet
                summary_data = self._flatten_summary(summary)
                df_summary = pd.DataFrame(
                    list(summary_data.items()),
                    columns=['Metric', 'Value']
                )
                df_summary.to_excel(
                    writer,
                    sheet_name='Summary',
                    index=False
                )
                
                # Format worksheets
                workbook = writer.book
                self._format_excel_workbook(workbook, writer.sheets)
            
            # Seek to beginning of stream
            output.seek(0)
            
            logger.debug("Excel export created successfully")
            return output
            
        except Exception as e:
            logger.error(f"Excel export failed: {str(e)}", exc_info=True)
            return BytesIO()
    
    def _flatten_summary(self, summary: Dict[str, Any]) -> Dict[str, str]:
        """
        Flatten nested summary dictionary for Excel export.
        
        Args:
            summary: Nested summary dictionary
            
        Returns:
            Flattened dictionary
        """
        flat = {}
        
        for key, value in summary.items():
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    flat[f"{key}_{sub_key}"] = str(sub_value)
            else:
                flat[key] = str(value)
        
        return flat
    
    def _extract_price(self, price_str: str) -> float:
        """
        Extract numeric price from formatted string.
        
        Args:
            price_str: Formatted price string (e.g., "€123,456")
            
        Returns:
            Numeric price value
        """
        try:
            # Remove currency symbol and commas
            numeric_str = price_str.replace('€', '').replace(',', '').strip()
            return float(numeric_str)
        except (ValueError, AttributeError):
            return 0.0
    
    def _extract_percentage(self, percent_str: str) -> float:
        """
        Extract numeric percentage from formatted string.
        
        Args:
            percent_str: Formatted percentage string (e.g., "85%")
            
        Returns:
            Numeric percentage value (0-100)
        """
        try:
            # Remove percentage symbol
            numeric_str = percent_str.replace('%', '').strip()
            return float(numeric_str)
        except (ValueError, AttributeError):
            return 0.0
    
    def _format_excel_workbook(
        self,
        workbook: Any,
        sheets: Dict[str, Any]
    ) -> None:
        """
        Apply formatting to Excel workbook.
        
        Args:
            workbook: xlsxwriter Workbook object
            sheets: Dictionary of worksheet objects
        """
        # Define formats
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#1f77b4',
            'font_color': 'white',
            'border': 1
        })
        
        # Define column widths for each sheet
        column_widths = {
            'Properties': {
                0: 6,   # Rank
                1: 30,  # Location
                2: 10,  # Type
                3: 10,  # Typology
                4: 12,  # Price
                5: 6,   # WCs
                6: 12,  # State
                7: 12,  # Transport
                8: 20,  # Agency
                9: 12,  # Match Score
                10: 30, # Link
            },
            'Summary': {
                0: 30,  # Metric
                1: 30,  # Value
            }
        }
        
        # Apply formatting to sheets
        for sheet_name, worksheet in sheets.items():
            if sheet_name in column_widths:
                # Set column widths
                for col_idx, width in column_widths[sheet_name].items():
                    worksheet.set_column(col_idx, col_idx, width)
    
    @property
    def agent(self) -> LlmAgent:
        """Get the underlying ADK LlmAgent instance."""
        return self._agent


def create_report_agent(model: str = ADKConfig.MODEL_NAME) -> LlmAgent:
    """
    Factory function to create a report agent.
    
    Args:
        model: LLM model name
        
    Returns:
        LlmAgent instance configured for reporting
    """
    report_agent = ReportAgent(model=model)
    return report_agent.agent


# Example usage
if __name__ == "__main__":
    import asyncio
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Create report agent
    agent = ReportAgent()
    
    # Example properties
    properties = [
        {
            "location": "Lisboa, Setúbal",
            "type": "flat",
            "typology": "T2",
            "price": 150000,
            "wcs": 1,
            "state": "used",
            "transport_distance": 10,
            "agency": "Idealista",
            "url": "https://www.idealista.pt/...",
            "match_score": 0.95,
        },
    ]
    
    requirements = {
        "location": "Lisboa",
        "property_type": "flat",
        "typology": ["T2"],
    }
    
    # Generate report
    report = asyncio.run(agent.generate_report(properties, requirements))
    
    print(f"Report generated with {len(report['table_data'])} properties")
    print(f"Summary: {report['summary']}")
