"""
GetMyHouse - Main Streamlit Application

This is the user interface for the GetMyHouse property search system.
It integrates with the Google ADK multi-agent architecture.

Author: José Neto
Course: 5-Day AI Agents Intensive with Google ADK
Date: November 2024
"""

import streamlit as st
import pandas as pd
import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import project modules
from src.config import UIConfig, SearchConfig, AppConfig, FeatureFlags, ADKConfig
from src.agents.coordinator import create_coordinator_agent
from src.tools.mock_search_tool import MockSearchTool

# Page configuration
st.set_page_config(
    page_title=UIConfig.PAGE_TITLE,
    page_icon=UIConfig.PAGE_ICON,
    layout=UIConfig.LAYOUT,
    initial_sidebar_state=UIConfig.INITIAL_SIDEBAR_STATE,
)


# =============================================================================
# Session State Management
# =============================================================================

def initialize_session_state():
    """Initialize Streamlit session state variables."""
    if UIConfig.SESSION_KEY_USER_ID not in st.session_state:
        st.session_state[UIConfig.SESSION_KEY_USER_ID] = f"user_{datetime.now().timestamp()}"
    
    if UIConfig.SESSION_KEY_SEARCH_HISTORY not in st.session_state:
        st.session_state[UIConfig.SESSION_KEY_SEARCH_HISTORY] = []
    
    if UIConfig.SESSION_KEY_LAST_SEARCH not in st.session_state:
        st.session_state[UIConfig.SESSION_KEY_LAST_SEARCH] = None
    
    if UIConfig.SESSION_KEY_RESULTS not in st.session_state:
        st.session_state[UIConfig.SESSION_KEY_RESULTS] = None
    
    if "coordinator_agent" not in st.session_state:
        st.session_state["coordinator_agent"] = None


def get_last_search_params() -> Optional[Dict[str, Any]]:
    """Get parameters from the last search."""
    return st.session_state.get(UIConfig.SESSION_KEY_LAST_SEARCH)


def save_search_params(params: Dict[str, Any]):
    """Save search parameters to session state."""
    st.session_state[UIConfig.SESSION_KEY_LAST_SEARCH] = params
    st.session_state[UIConfig.SESSION_KEY_SEARCH_HISTORY].append({
        "timestamp": datetime.now(),
        "params": params
    })


# =============================================================================
# UI Components
# =============================================================================

def render_header():
    """Render the application header."""
    st.title("🏠 GetMyHouse")
    st.markdown("### AI-Powered Property Search")
    st.markdown("*Built with Google Agent Development Kit (ADK)*")
    st.divider()


def render_sidebar():
    """Render the sidebar with application info."""
    with st.sidebar:
        st.header("ℹ️ About")
        st.markdown(f"""
        **GetMyHouse** is an AI-powered property search system 
        demonstrating multi-agent architecture using Google ADK.
        
        **Version:** {AppConfig.VERSION}  
        **Environment:** {AppConfig.ENV}
        """)
        
        st.divider()
        
        st.header("🎓 ADK Concepts")
        st.markdown("""
        - ✅ Multi-Agent System
        - ✅ LLM Agents (Gemini)
        - ✅ Custom Tools (MCP)
        - ✅ Workflow Orchestration
        - ✅ Session Management
        """)
        
        st.divider()
        
        st.header("📊 Search Statistics")
        total_searches = len(st.session_state.get(UIConfig.SESSION_KEY_SEARCH_HISTORY, []))
        st.metric("Total Searches", total_searches)
        
        if st.session_state.get(UIConfig.SESSION_KEY_RESULTS):
            results = st.session_state[UIConfig.SESSION_KEY_RESULTS]
            if "table_data" in results:
                st.metric("Last Results", len(results["table_data"]))


def update_selected_country():
    """
    Callback function to update selected country in session state.
    
    This is called when the country selectbox changes, allowing us to
    display currency info outside the form (v2.0.2).
    """
    if "country_select" in st.session_state:
        st.session_state.selected_country = st.session_state.country_select
        logger.debug(f"Country changed to: {st.session_state.selected_country}")


def render_search_form() -> Optional[Dict[str, Any]]:
    """
    Render the property search form.
    
    Returns:
        Dictionary with search parameters if form is submitted, None otherwise
    """
    st.header("🔍 Property Search")
    
    # Initialize form counter for clearing (v2.1.5)
    if "form_counter" not in st.session_state:
        st.session_state.form_counter = 0
    
    # Initialize selected country in session state (v2.0.2)
    if "selected_country" not in st.session_state:
        st.session_state.selected_country = SearchConfig.DEFAULT_COUNTRY
    
    # Country Selection (OUTSIDE form to allow real-time updates) - v2.0.2
    st.subheader("🌍 Select Country (195 countries supported!)")
    countries = SearchConfig.get_supported_countries()
    country = st.selectbox(
        "Country *",
        options=countries,
        index=countries.index(st.session_state.selected_country) if st.session_state.selected_country in countries else 0,
        help="Select the country where you want to search for properties",
        key="country_select",
        on_change=update_selected_country
    )
    
    # Display currency info (v2.0.2)
    # This updates immediately when country is selected
    currency_info = SearchConfig.get_currency_info(st.session_state.selected_country)
    st.info(f"💰 **Currency for {st.session_state.selected_country}**: {currency_info['symbol']} ({currency_info['currency']})")
    
    st.markdown("---")  # Visual separator
    
    # Clear form button (MUST be outside form)
    col_btn1, col_btn2, col_btn3 = st.columns([2, 1, 2])
    with col_btn2:
        if st.button("🗑️ Clear All", key="clear_form_btn", type="secondary", use_container_width=True):
            # Increment form counter to force widget recreation
            st.session_state.form_counter += 1
            # Clear search results
            if UIConfig.SESSION_KEY_RESULTS in st.session_state:
                del st.session_state[UIConfig.SESSION_KEY_RESULTS]
            # Reset country to default
            st.session_state.selected_country = SearchConfig.DEFAULT_COUNTRY
            st.success("✅ Form cleared!")
            time.sleep(0.3)
            st.rerun()
    
    with st.form("search_form"):
        # First row: Location only (Country is now outside form)
        col1_1 = st.columns(1)[0]
        
        with col1_1:
            # Location
            location = st.text_input(
                "Location *",
                value="",
                placeholder="e.g., City, metropolitan area, state, region, etc.",
                help="City, metropolitan area, state, or region",
                key=f"search_location_{st.session_state.form_counter}"
            )
        
        # Second row: Distance and Public Transport
        col2_1, col2_2 = st.columns(2)
        
        with col2_1:
            # Distance to Location (km)
            distance = st.selectbox(
                "Max Distance to Location (km)",
                options=SearchConfig.DISTANCE_OPTIONS,
                index=5,  # Default to "any"
                help="Maximum acceptable distance from specified location (in kilometers)",
                key=f"distance_{st.session_state.form_counter}"
            )
        
        with col2_2:
            # Public Transport
            public_transport = st.selectbox(
                "Public Transport (walking minutes)",
                options=SearchConfig.TRANSPORT_OPTIONS,
                index=3,
                help="Maximum acceptable walking time to public transport (in minutes)",
                key=f"transport_{st.session_state.form_counter}"
            )
        
        # Third row: Property Type and Typology
        col3_1, col3_2 = st.columns(2)
        
        with col3_1:
            # Property Type
            property_type = st.selectbox(
                "Property Type *",
                options=SearchConfig.PROPERTY_TYPES,
                index=0,  # Default to "any"
                key=f"property_type_{st.session_state.form_counter}"
            )
        
        with col3_2:
            # Typology (multi-select)
            typology = st.multiselect(
                "Typology *",
                options=SearchConfig.TYPOLOGIES,
                default=[],
                help="Select one or more bedroom configurations",
                key=f"typology_{st.session_state.form_counter}"
            )
        
        # Fourth row: WCs and Usage State
        col4_1, col4_2 = st.columns(2)
        
        with col4_1:
            # Number of WCs
            wcs = st.selectbox(
                "Number of WCs",
                options=[1, 2, 3, "any"],
                index=3,
                help="Number of bathrooms/WCs",
                key=f"wcs_{st.session_state.form_counter}"
            )
        
        with col4_2:
            # Usage State
            usage_state = st.selectbox(
                "Usage State",
                options=SearchConfig.USAGE_STATES,
                index=0,  # Default: "any"
                help="Condition of the property",
                key=f"usage_state_{st.session_state.form_counter}"
            )
        
        # Fifth row: Max Results and Price Range (Currency removed - shown at top)
        col5_1, col5_2, col5_3 = st.columns([1, 1.5, 1.5])
        
        with col5_1:
            # Max Results (NEW in v2.0)
            max_results = st.selectbox(
                "Max Results",
                options=SearchConfig.MAX_RESULTS_OPTIONS,
                index=1,  # Default to 20
                help="Maximum number of properties to return",
                key=f"max_results_{st.session_state.form_counter}"
            )
        
        with col5_2:
            # Price From
            price_min = st.number_input(
                "Price From",
                min_value=0,
                value=0,
                step=10000,
                format="%d",
                key=f"price_min_{st.session_state.form_counter}"
            )
        
        with col5_3:
            # Price To
            price_max = st.number_input(
                "Price To",
                min_value=0,
                value=500000,
                step=10000,
                format="%d",
                key=f"price_max_{st.session_state.form_counter}"
            )
        
        # Sixth row: Other Requirements (full width)
        st.markdown("**Additional Requirements** (optional)")
        other_requirements = st.text_area(
            "Other Requirements",
            value="",
            key=f"other_requirements_{st.session_state.form_counter}",
            placeholder="Any other specific requirements (e.g., 'must have parking', 'near school', etc.)",
            height=100,
            label_visibility="collapsed"
        )
        
        # Submit button
        submitted = st.form_submit_button(
            "🔍 Search Properties",
            use_container_width=True,
            type="primary"
        )
        
        if submitted:
            # Get country from session state (v2.0.2 - country is outside form)
            country = st.session_state.selected_country
            
            # Validate required fields
            if not country or not location or not typology:
                st.error("❌ Please fill in all required fields: Country, Location and Typology")
                return None
            
            # Calculate currency based on selected country (v2.0)
            currency_info = SearchConfig.get_currency_info(country)
            currency = currency_info.get("currency", "EUR")
            currency_symbol = currency_info.get("symbol", "€")
            
            # Build parameters dictionary
            params = {
                "country": country,
                "location": location,
                "property_type": property_type,
                "typology": typology,
                "currency": currency,
                "currency_symbol": currency_symbol,  # NEW v2.0
                "max_results": max_results,  # NEW v2.0
                "price_min": price_min,
                "price_max": price_max,
                "distance": distance,
                "wcs": wcs if wcs != "any" else None,
                "usage_state": usage_state if usage_state != "any" else None,
                "public_transport": public_transport if public_transport != "any" else None,
                "other_requirements": other_requirements if other_requirements else None,
            }
            
            return params
    
    return None


def render_results(results: Dict[str, Any]):
    """
    Render search results.
    
    Args:
        results: Dictionary containing search results from the coordinator agent
    """
    if not results:
        return
    
    st.header("📋 Search Results")
    
    # Info about link types
    st.info("""
    🔗 **About Property Links:**
    - 🎯 **Direct Links**: Go directly to property listing (when available)
    - 🔍 **Search Links**: Google search for the property (when direct link unavailable)
    
    Some links may not work if properties were sold or URLs changed.
    """)
    
    # Check for errors
    if "error" in results:
        st.error(f"❌ Search failed: {results['error']}")
        return
    
    # Get results data
    table_data = results.get("table_data", [])
    summary = results.get("summary", {})
    
    if not table_data:
        st.warning("🔍 No properties found matching your criteria. Try adjusting your search parameters.")
        return
    
    # Display summary
    with st.expander("📊 Search Summary", expanded=True):
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Results", summary.get("total", 0))
        
        with col2:
            avg_price = summary.get("price_range", {}).get("avg", "N/A")
            st.metric("Average Price", avg_price)
        
        with col3:
            avg_score = summary.get("match_score", {}).get("avg", "N/A")
            st.metric("Avg Match Score", avg_score)
        
        with col4:
            best_score = summary.get("match_score", {}).get("best", "N/A")
            st.metric("Best Match", best_score)
    
    # Display properties table
    st.subheader(f"🏠 Top {len(table_data)} Properties")
    
    # Convert to DataFrame for better display
    df = pd.DataFrame(table_data)
    
    # Display as interactive table
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Link": st.column_config.LinkColumn(
                "Property Link",
                help="Click to view property details",
                display_text="View Property"
            ),
            "Match Score": st.column_config.ProgressColumn(
                "Match Score",
                help="How well this property matches your requirements",
                format="%s",
                min_value=0,
                max_value=100,
            ),
        }
    )
    
    # Export to Excel
    if results.get("excel_data"):
        st.download_button(
            label="📥 Download Results (Excel)",
            data=results["excel_data"].getvalue(),
            file_name=f"getmyhouse_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )


# =============================================================================
# Agent Integration
# =============================================================================

async def execute_search(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute property search using the coordinator agent.
    
    Args:
        params: Search parameters
        
    Returns:
        Dictionary with search results
    """
    try:
        logger.info(f"Executing search with params: {params}")
        
        # Get country from params (v2.0.2 - multi-country support)
        country = params.get("country", "Portugal")
        location = params.get("location", "")
        logger.info(f"Searching in {location}, {country}")
        
        # v2.1.0: CORRECT Architecture - Discovery Agent + LLM Search
        # NO hardcoded scrapers! Universal system for 195 countries!
        logger.info("🎯 Multi-Agent Workflow Starting...")
        
        # Phase 1: Real Property Search (Discovery + LLM + Google Search)
        logger.info("📡 Phase 1: Discovery + Property Search")
        properties = []
        
        if FeatureFlags.ENABLE_REAL_SCRAPING:
            try:
                logger.info(f"  🔍 ENABLE_REAL_SCRAPING is TRUE - Starting real search...")
                logger.info(f"  🔍 Using Discovery Agent + LLM for {location}, {country}...")
                
                from src.tools.real_search_tool import RealSearchTool
                logger.info(f"  ✅ RealSearchTool imported successfully")
                
                real_tool = RealSearchTool()
                logger.info(f"  ✅ RealSearchTool instance created")
                
                # Search using Discovery + LLM + Google Search
                # 1. Discovery Agent finds real estate sites for country
                # 2. LLM searches Google with site: filters
                # 3. LLM extracts properties from search snippets
                # Works for ANY country!
                logger.info(f"  🚀 Calling real_tool.search_properties()...")
                logger.info(f"     Parameters: country={country}, location={location}")
                logger.info(f"     Max results: {params.get('max_results', 20)}")
                
                properties = await real_tool.search_properties(
                    requirements=params,
                    max_results=params.get("max_results", 20)
                )
                
                logger.info(f"  ✅ real_tool.search_properties() returned!")
                logger.info(f"  ✅ Properties count: {len(properties) if properties else 0}")
                
                if properties:
                    logger.info(f"  ✅ Found {len(properties)} REAL properties from web!")
                else:
                    logger.warning(f"  ⚠️  No properties found in web search")
                    logger.info(f"  💡 Fallback to mock data...")
                    
            except Exception as e:
                import traceback
                logger.error(f"  ❌ Real search failed with exception!")
                logger.error(f"  ❌ Error type: {type(e).__name__}")
                logger.error(f"  ❌ Error message: {str(e)}")
                logger.error(f"  ❌ Full traceback:")
                logger.error(traceback.format_exc())
                logger.info(f"  💡 Fallback to mock data...")
        else:
            logger.warning(f"  ⚠️  ENABLE_REAL_SCRAPING is FALSE!")
            logger.info(f"  ⏭️  Real search disabled (ENABLE_REAL_SCRAPING=false)")
        
        # Fallback to mock ONLY if real search returned nothing
        if not properties:
            logger.info("📡 Phase 2: Mock Data Fallback")
            logger.info(f"  🔄 Using MockSearchTool as fallback...")
            
            from src.tools.mock_search_tool import MockSearchTool
            mock_tool = MockSearchTool()
            
            properties = mock_tool.search(
                country=country,
                location=location,
                property_type=params.get("property_type"),
                typology=params.get("typology"),
                price_min=params.get("price_min", 0),
                price_max=params.get("price_max", 10000000),
                wcs=params.get("wcs"),
                usage_state=params.get("usage_state"),
                transport_distance=params.get("public_transport"),
            )
            
            logger.info(f"  ✅ Mock data provided {len(properties)} properties")
        
        logger.info(f"✅ Total properties: {len(properties)}")
        
        # Phase 4: Filter properties
        logger.info("📡 Phase 4: Filter & Rank")
        from src.agents.filter_agent import FilterAgent
        filter_agent = FilterAgent()
        
        filtered_properties = await filter_agent.filter_and_rank(
            properties=properties,
            requirements=params,
            max_results=params.get("max_results", 20)
        )
        logger.info(f"  ✅ Filtered to {len(filtered_properties)} top properties")
        
        # Phase 5: Generate report
        logger.info("📡 Phase 5: Report Generation")
        from src.agents.report_agent import ReportAgent
        report_agent = ReportAgent()
        
        results = await report_agent.generate_report(
            properties=filtered_properties,
            requirements=params
        )
        logger.info(f"  ✅ Report generated successfully")
        
        logger.info("🎉 Multi-Agent Workflow Complete!")
        
        return results
        
    except Exception as e:
        logger.error(f"Search failed: {str(e)}", exc_info=True)
        return {
            "error": str(e),
            "table_data": [],
            "summary": {}
        }


def run_search(params: Dict[str, Any]):
    """
    Run the search and update UI.
    
    Args:
        params: Search parameters
    """
    with st.spinner("🤖 AI agents are searching for properties..."):
        # Run async search in sync context
        results = asyncio.run(execute_search(params))
        
        # Save results to session state
        st.session_state[UIConfig.SESSION_KEY_RESULTS] = results
        save_search_params(params)
        
        return results


# =============================================================================
# Main Application
# =============================================================================

def main():
    """Main application entry point."""
    # Log configuration
    logger.info("=" * 60)
    logger.info(f"🚀 GetMyHouse v{AppConfig.VERSION} Starting...")
    logger.info(f"📊 Configuration:")
    logger.info(f"   ENABLE_REAL_SCRAPING = {FeatureFlags.ENABLE_REAL_SCRAPING}")
    logger.info(f"   Model: {ADKConfig.MODEL_NAME}")
    logger.info("=" * 60)
    
    # Initialize session state
    initialize_session_state()
    
    # Render UI components
    render_header()
    render_sidebar()
    
    # Render search form and get parameters if submitted
    search_params = render_search_form()
    
    # Execute search if form was submitted
    if search_params:
        results = run_search(search_params)
        render_results(results)
    
    # Display previous results if they exist (after page refresh)
    elif st.session_state.get(UIConfig.SESSION_KEY_RESULTS):
        render_results(st.session_state[UIConfig.SESSION_KEY_RESULTS])
    
    # Footer
    st.divider()
    st.markdown("""
    <div style='text-align: center; color: gray;'>
        <p>GetMyHouse v1.0 | Built with ❤️ using Google ADK | November 2024</p>
        <p>Capstone Project - 5-Day AI Agents Intensive</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
