import streamlit as st
import requests
import json
from dotenv import load_dotenv
import os
from openai import OpenAI
import pandas as pd

st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        .stAppDeployButton {display:none;}
        footer {visibility: hidden;}
        .stMainBlockContainer {padding: 2rem 1rem 2rem 1rem;}
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'show_contact_congress' not in st.session_state:
    st.session_state.show_contact_congress = False
if 'show_analyze_bill' not in st.session_state:
    st.session_state.show_analyze_bill = False
if 'show_house_activity' not in st.session_state:
    st.session_state.show_house_activity = False
if 'lookup_results' not in st.session_state:
    st.session_state.lookup_results = None
if 'selected_bill' not in st.session_state:
    st.session_state.selected_bill = None

def reset_filters():
    """Reset all filter session state to default values"""
    # Reset backend filter state
    st.session_state.filter_action_start_date = None
    st.session_state.filter_action_end_date = None
    st.session_state.filter_chamber = "All"
    st.session_state.filter_legislative_stages = []
    st.session_state.filter_min_cosponsors = 0
    st.session_state.filters_applied = False
    
    # Clear widget keys to force UI reset
    widget_keys = [
        'action_start_date',
        'action_end_date', 
        'chamber_filter',
        'legislative_stages',
        'min_cosponsors'
    ]
    
    for key in widget_keys:
        if key in st.session_state:
            del st.session_state[key]

# Load environment variables from .env file
load_dotenv(override=True)

# Get API keys from environment
CONGRESS_API_KEY = os.getenv("CONGRESS_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def get_representatives_from_address(address: str):
    """
    Use OpenAI to determine congressional representatives (House and Senate) 
    for a given address, including their local and DC phone numbers.
    """
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    prompt = f"""
    Given the following address, please identify:
    1. The U.S. House Representative for this district
    2. Both U.S. Senators for this state
    
    For each representative, provide:
    - Full name
    - Party affiliation
    - District (for House member only)
    - DC office phone number
    - Local/district office phone number
    
    Address: {address}
    
    Return the information in JSON format with this structure:
    {{
        "house_representative": {{
            "name": "Full Name",
            "party": "Party",
            "district": "State-District",
            "dc_phone": "(202) XXX-XXXX",
            "local_phone": "(XXX) XXX-XXXX"
        }},
        "senators": [
            {{
                "name": "Full Name",
                "party": "Party",
                "dc_phone": "(202) XXX-XXXX",
                "local_phone": "(XXX) XXX-XXXX"
            }}
        ]
    }}
    """
    
    response = client.chat.completions.create(
        model="gpt-4.1-nano",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that provides accurate information about U.S. congressional representatives and their contact information. Always return valid JSON."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        response_format={"type": "json_object"}
    )
    
    result = json.loads(response.choices[0].message.content)
    return result

st.markdown("<h1 style='text-align: center;'>Get Political. Take Action.</h1>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("Congressional Activity", type="primary" if st.session_state.show_house_activity else "secondary", use_container_width=True):
        st.session_state.show_house_activity = True
        st.session_state.show_analyze_bill = False
        st.session_state.show_contact_congress = False
        st.session_state.lookup_results = None
        st.session_state.selected_bill = None
        st.rerun()

with col2:
    if st.button("Analyze Bill", type="primary" if st.session_state.show_analyze_bill else "secondary", use_container_width=True):
        st.session_state.show_analyze_bill = True
        st.session_state.show_contact_congress = False
        st.session_state.show_house_activity = False
        st.session_state.lookup_results = None
        st.rerun()

with col3:
    if st.button("Contact Congress", type="primary" if st.session_state.show_contact_congress else "secondary", use_container_width=True):
        st.session_state.show_contact_congress = True
        st.session_state.show_analyze_bill = False
        st.session_state.show_house_activity = False
        st.session_state.selected_bill = None
        st.rerun()

if st.session_state.show_house_activity:
    st.markdown("<h3 style='text-align: center;'>Congressional Activity</h3>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Select a bill from the table below to analyze it in detail.</p>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Utilize left pane filters to refine list of bills.</p>", unsafe_allow_html=True)
    
    # Initialize filter state if not exists
    if 'filter_action_start_date' not in st.session_state:
        st.session_state.filter_action_start_date = None
    if 'filter_action_end_date' not in st.session_state:
        st.session_state.filter_action_end_date = None
    if 'filter_chamber' not in st.session_state:
        st.session_state.filter_chamber = "All"
    if 'filter_legislative_stages' not in st.session_state:
        st.session_state.filter_legislative_stages = []
    
    if 'filter_min_cosponsors' not in st.session_state:
        st.session_state.filter_min_cosponsors = 0
    
    if 'filters_applied' not in st.session_state:
        st.session_state.filters_applied = False
    if 'default_bills_df' not in st.session_state:
        st.session_state.default_bills_df = None
    
    # Sidebar filters
    with st.sidebar:
        st.header("Filter Bills")
        
        # Action date range filter
        st.subheader("Action Date Range")
        col1, col2 = st.columns(2)
        with col1:
            action_start_date = st.date_input("From", value=st.session_state.filter_action_start_date, key="action_start_date")
        with col2:
            action_end_date = st.date_input("To", value=st.session_state.filter_action_end_date, key="action_end_date")
        
        # Chamber filter
        st.subheader("Chamber")
        chamber_filter = st.selectbox(
            "Origin Chamber",
            options=["All", "House", "Senate"],
            index=["All", "House", "Senate"].index(st.session_state.filter_chamber),
            key="chamber_filter"
        )
        
        # Legislative stage filter
        st.subheader("Legislative Stage")
        legislative_stages = st.multiselect(
            "Select stages",
            options=[
                "Introduced",
                "Referred to Committee",
                "Reported by Committee",
                "Passed House",
                "Passed Senate",
                "To President",
                "Became Law"
            ],
            default=st.session_state.filter_legislative_stages,
            key="legislative_stages"
        )
        
        
        
        # Cosponsors filter
        st.subheader("Cosponsors")
        min_cosponsors = st.number_input(
            "Minimum number",
            min_value=0,
            value=st.session_state.filter_min_cosponsors,
            step=1,
            key="min_cosponsors"
        )
        
        # Apply filter button
        apply_filters = st.button("Apply Filters", type="primary", use_container_width=True)
        
        # Update session state when Apply Filters is clicked
        if apply_filters:
            st.session_state.filter_action_start_date = action_start_date
            st.session_state.filter_action_end_date = action_end_date
            st.session_state.filter_chamber = chamber_filter
            st.session_state.filter_legislative_stages = legislative_stages
            st.session_state.filter_min_cosponsors = min_cosponsors
            st.session_state.filters_applied = True
        
        # Clear filters button
        if st.button("Clear Filters", use_container_width=True, key="clear_filters_btn"):
            reset_filters()
            st.rerun()
    
    # Load default unfiltered view first (if not already loaded)
    if st.session_state.default_bills_df is None:
        with st.spinner("Fetching recent bills..."):
            congress = '119'
            recent_bills_url = f'https://api.congress.gov/v3/bill/{congress}'
            
            recent_bills_params = {
                'api_key': CONGRESS_API_KEY,
                'limit': 50,
                'sort': 'updateDate+desc'
            }
            
            recent_bills_response = requests.get(recent_bills_url, params=recent_bills_params)
            recent_bills_data = recent_bills_response.json()
            
            if recent_bills_response.status_code == 200 and 'bills' in recent_bills_data:
                import pandas as pd
                
                # Create a DataFrame of recent bills for consideration
                bills_to_consider = []
                
                for bill in recent_bills_data['bills']:
                    # Get cosponsor count
                    cosponsor_count = 0
                    if 'cosponsors' in bill and 'count' in bill['cosponsors']:
                        cosponsor_count = bill['cosponsors']['count']
                    
                    bill_dict = {
                        'bill_number': f"{bill['type']} {bill['number']}",
                        'title': bill['title'],
                        'origin_chamber': bill['originChamber'],
                        'latest_action': bill['latestAction']['text'],
                        'action_date': bill['latestAction']['actionDate'],
                        'update_date': bill['updateDate'],
                        'congress': bill['congress'],
                        'url': bill['url'],
                        'policy_area': bill.get('policyArea', {}).get('name', 'Not Assigned') if 'policyArea' in bill and bill['policyArea'] else 'Not Assigned',
                        'cosponsor_count': cosponsor_count
                    }
                    bills_to_consider.append(bill_dict)
                
                # Create DataFrame
                bills_to_consider_df = pd.DataFrame(bills_to_consider)
                bills_to_consider_df['action_date'] = pd.to_datetime(bills_to_consider_df['action_date'])
                bills_to_consider_df['update_date'] = pd.to_datetime(bills_to_consider_df['update_date'])
                bills_to_consider_df = bills_to_consider_df.sort_values('update_date', ascending=False)
                
                # Store in session state
                st.session_state.default_bills_df = bills_to_consider_df
            else:
                st.error("Failed to fetch recent bills data.")
                st.session_state.default_bills_df = pd.DataFrame()
    
    # Only fetch filtered data when Apply Filters is clicked and filters are active
    if st.session_state.filters_applied:
        with st.spinner("Fetching filtered bills..."):
            congress = '119'
            recent_bills_url = f'https://api.congress.gov/v3/bill/{congress}'
            
            recent_bills_params = {
                'api_key': CONGRESS_API_KEY,
                'limit': 50,
                'sort': 'updateDate+desc'
            }
            
            # Add API-level filter parameters (using session state values)
            if st.session_state.filter_action_start_date:
                recent_bills_params['fromDateTime'] = st.session_state.filter_action_start_date.strftime('%Y-%m-%dT00:00:00Z')
            if st.session_state.filter_action_end_date:
                recent_bills_params['toDateTime'] = st.session_state.filter_action_end_date.strftime('%Y-%m-%dT23:59:59Z')
            
            recent_bills_response = requests.get(recent_bills_url, params=recent_bills_params)
            recent_bills_data = recent_bills_response.json()
            
            if recent_bills_response.status_code == 200 and 'bills' in recent_bills_data:
                import pandas as pd
                
                # Create a DataFrame of recent bills
                bills_to_consider = []
                
                for bill in recent_bills_data['bills']:
                    # Get cosponsor count
                    cosponsor_count = 0
                    if 'cosponsors' in bill and 'count' in bill['cosponsors']:
                        cosponsor_count = bill['cosponsors']['count']
                    
                    bill_dict = {
                        'bill_number': f"{bill['type']} {bill['number']}",
                        'title': bill['title'],
                        'origin_chamber': bill['originChamber'],
                        'latest_action': bill['latestAction']['text'],
                        'action_date': bill['latestAction']['actionDate'],
                        'update_date': bill['updateDate'],
                        'congress': bill['congress'],
                        'url': bill['url'],
                        'policy_area': bill.get('policyArea', {}).get('name', 'Not Assigned') if 'policyArea' in bill and bill['policyArea'] else 'Not Assigned',
                        'cosponsor_count': cosponsor_count
                    }
                    bills_to_consider.append(bill_dict)
                
                # Create DataFrame
                bills_to_consider_df = pd.DataFrame(bills_to_consider)
                bills_to_consider_df['action_date'] = pd.to_datetime(bills_to_consider_df['action_date'])
                bills_to_consider_df['update_date'] = pd.to_datetime(bills_to_consider_df['update_date'])
                bills_to_consider_df = bills_to_consider_df.sort_values('update_date', ascending=False)
                
                # Apply client-side filters (using session state values)
                filtered_df = bills_to_consider_df.copy()
                
                # Filter by chamber
                if st.session_state.filter_chamber != "All":
                    filtered_df = filtered_df[filtered_df['origin_chamber'] == st.session_state.filter_chamber]
                
                # Filter by legislative stage (based on latest action text)
                if st.session_state.filter_legislative_stages:
                    stage_patterns = []
                    for stage in st.session_state.filter_legislative_stages:
                        if stage == "Introduced":
                            stage_patterns.append("Introduced")
                        elif stage == "Referred to Committee":
                            stage_patterns.append("Referred to")
                        elif stage == "Reported by Committee":
                            stage_patterns.append("Reported")
                        elif stage == "Passed House":
                            stage_patterns.append("Passed House")
                        elif stage == "Passed Senate":
                            stage_patterns.append("Passed Senate")
                        elif stage == "To President":
                            stage_patterns.append("Presented to President")
                        elif stage == "Became Law":
                            stage_patterns.append("Became Public Law")
                    
                    if stage_patterns:
                        pattern = '|'.join(stage_patterns)
                        filtered_df = filtered_df[filtered_df['latest_action'].str.contains(pattern, case=False, na=False)]
                
                # Filter by minimum cosponsors
                if st.session_state.filter_min_cosponsors > 0:
                    filtered_df = filtered_df[filtered_df['cosponsor_count'] >= st.session_state.filter_min_cosponsors]
                
                bills_to_consider_df = filtered_df
                
                if len(bills_to_consider_df) == 0:
                    st.warning("No bills match the selected filters. Try adjusting your criteria.")
                else:
                    st.success(f"Found {len(bills_to_consider_df)} bills matching your filters.")
            else:
                st.error("Failed to fetch bills data from API.")
                bills_to_consider_df = pd.DataFrame()
    else:
        # Use default unfiltered view (no API call)
        bills_to_consider_df = st.session_state.default_bills_df if st.session_state.default_bills_df is not None else pd.DataFrame()
    
    # Display active filters summary just above the table
    active_filters = []
    
    # Format action date range
    if st.session_state.filter_action_start_date and st.session_state.filter_action_end_date:
        active_filters.append(f"Action Date: {st.session_state.filter_action_start_date.strftime('%Y-%m-%d')} to {st.session_state.filter_action_end_date.strftime('%Y-%m-%d')}")
    elif st.session_state.filter_action_start_date:
        active_filters.append(f"Action Date From: {st.session_state.filter_action_start_date.strftime('%Y-%m-%d')}")
    elif st.session_state.filter_action_end_date:
        active_filters.append(f"Action Date To: {st.session_state.filter_action_end_date.strftime('%Y-%m-%d')}")
    
    if st.session_state.filter_chamber != "All":
        active_filters.append(f"Chamber: {st.session_state.filter_chamber}")
    
    if st.session_state.filter_legislative_stages:
        stages_str = ", ".join(st.session_state.filter_legislative_stages)
        active_filters.append(f"Legislative Stage: {stages_str}")
    
    
    
    if st.session_state.filter_min_cosponsors > 0:
        active_filters.append(f"Min Cosponsors: {st.session_state.filter_min_cosponsors}")
    
    if active_filters:
        filters_summary = " | ".join(active_filters)
        st.info(f"**Active Filters:** {filters_summary}")
    else:
        st.info("**No filters applied**")
    
    # Display the interactive table with row selection
    if len(bills_to_consider_df) > 0:
        # Ensure 'stage' column exists (derive from latest_action if needed)
        if 'legislative_stage' not in bills_to_consider_df.columns and 'stage' not in bills_to_consider_df.columns:
            # Derive stage from latest_action text
            def derive_stage(action_text):
                if pd.isna(action_text):
                    return 'Unknown'
                action_lower = str(action_text).lower()
                if 'became public law' in action_lower or 'became law' in action_lower:
                    return 'Became Law'
                elif 'presented to president' in action_lower:
                    return 'To President'
                elif 'passed senate' in action_lower:
                    return 'Passed Senate'
                elif 'passed house' in action_lower:
                    return 'Passed House'
                elif 'reported' in action_lower:
                    return 'Reported by Committee'
                elif 'referred to' in action_lower:
                    return 'Referred to Committee'
                elif 'introduced' in action_lower:
                    return 'Introduced'
                else:
                    return 'In Progress'
            
            bills_to_consider_df['stage'] = bills_to_consider_df['latest_action'].apply(derive_stage)
        elif 'legislative_stage' in bills_to_consider_df.columns and 'stage' not in bills_to_consider_df.columns:
            bills_to_consider_df['stage'] = bills_to_consider_df['legislative_stage']
        
        # Define display columns with 'stage' right after 'origin_chamber'
        display_columns = ['bill_number', 'title', 'origin_chamber', 'stage', 'action_date', 'latest_action']
        if st.session_state.filter_min_cosponsors > 0:
            display_columns.insert(4, 'cosponsor_count')
        
        # Ensure 'committee' column is not in display_columns
        if 'committee' in display_columns:
            display_columns.remove('committee')
        
        event = st.dataframe(
            bills_to_consider_df[display_columns],
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
            column_config={
                "bill_number": st.column_config.TextColumn(
                    "Bill Number",
                    width="small"
                ),
                "title": st.column_config.TextColumn(
                    "Title",
                    width="large"
                ),
                "origin_chamber": st.column_config.TextColumn(
                    "Chamber",
                    width="small"
                ),
                "stage": st.column_config.TextColumn(
                    "Stage",
                    width="medium"
                ),
                "cosponsor_count": st.column_config.NumberColumn(
                    "Cosponsors",
                    width="small"
                ),
                "action_date": st.column_config.DateColumn(
                    "Action Date",
                    format="YYYY-MM-DD",
                    width="small"
                ),
                "latest_action": st.column_config.TextColumn(
                    "Latest Action",
                    width="medium"
                )
            }
        )
        
        # Handle row selection
        if event.selection and event.selection.rows:
            selected_row_index = event.selection.rows[0]
            selected_bill_row = bills_to_consider_df.iloc[selected_row_index]
            
            # Store the entire row in session state
            st.session_state.selected_bill = selected_bill_row.to_dict()
            
            # Switch to analyze bill view
            st.session_state.show_analyze_bill = True
            st.session_state.show_house_activity = False
            st.session_state.show_contact_congress = False
            st.rerun()
    else:
        st.info("No bills to display. Try adjusting your filters or check back later.")

if st.session_state.show_contact_congress:
    # Hide sidebar on Contact Congress page
    st.markdown("""
        <style>
            [data-testid="stSidebar"] {
                display: none !important;
            }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown("<h3 style='text-align: center;'>Find Your Members of Congress</h3>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Enter your address below to find your U.S. Senators and House Representative, along with their contact information.</p>", unsafe_allow_html=True)
    
    addr = st.text_input("Enter your address", placeholder="123 Mean Street City State")
    
    if st.button("Search", type="primary", key="lookup_btn"):
        if not addr.strip():
            st.error("Please enter an address.")
        else:
            try:
                if not OPENAI_API_KEY:
                    st.error("Set OPENAI_API_KEY in your .env")
                else:
                    with st.spinner("Looking up your representatives..."):
                        representatives = get_representatives_from_address(addr)
                        st.session_state.lookup_results = representatives
            except Exception as ex:
                st.error(f"Error: {str(ex)}")
    
    # Display results if they exist
    if st.session_state.lookup_results:
        results = st.session_state.lookup_results
        
        st.markdown("## Your U.S. Senators")
        if 'senators' in results and results['senators']:
            for senator in results['senators']:
                with st.container(border=True):
                    st.markdown(f"### {senator['name']}")
                    st.caption(f"{senator.get('party', '')}")
                    st.markdown(f"**DC Phone:** {senator.get('dc_phone', 'N/A')}")
                    st.markdown(f"**Local Phone:** {senator.get('local_phone', 'N/A')}")
        else:
            st.warning("No senators found.")
        
        st.markdown("## Your U.S. House Representative")
        if 'house_representative' in results:
            house = results['house_representative']
            with st.container(border=True):
                st.markdown(f"### {house['name']}")
                st.caption(f"{house.get('party', '')} • {house.get('district', '')}")
                st.markdown(f"**DC Phone:** {house.get('dc_phone', 'N/A')}")
                st.markdown(f"**Local Phone:** {house.get('local_phone', 'N/A')}")
        else:
            st.warning("No House representative found.")

if st.session_state.show_analyze_bill:
    # Hide sidebar on Analyze Bill page
    st.markdown("""
        <style>
            [data-testid="stSidebar"] {
                display: none !important;
            }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown("<h3 style='text-align: center;'>Analyze a Congressional Bill</h3>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Enter bill details below to analyze</p>", unsafe_allow_html=True)
    
    # Initialize widget values from selected bill if available
    if 'analyze_bill_type' not in st.session_state:
        st.session_state.analyze_bill_type = 'hr'
    if 'analyze_congress' not in st.session_state:
        st.session_state.analyze_congress = '119'
    if 'analyze_bill_number' not in st.session_state:
        st.session_state.analyze_bill_number = ''
    
    # Check if we have a selected bill from Congressional Activity and auto-populate
    if st.session_state.get('selected_bill') is not None:
        selected_data = st.session_state.selected_bill
        
        # Parse bill_type and bill_number from bill_number (e.g., "hr 2316")
        bill_parts = selected_data['bill_number'].split()
        if len(bill_parts) == 2:
            st.session_state.analyze_bill_type = bill_parts[0].lower()
            st.session_state.analyze_bill_number = bill_parts[1]
        
        st.session_state.analyze_congress = str(selected_data['congress'])
        
        # Clear selected_bill so we don't auto-populate again
        st.session_state.selected_bill = None
    
    # Always show manual input fields
    col1, col2, col3 = st.columns(3)
    
    with col1:
        bill_type = st.selectbox(
            "Bill Type",
            options=['hr', 's', 'hjres', 'sjres', 'hconres', 'sconres', 'hres', 'sres'],
            index=['hr', 's', 'hjres', 'sjres', 'hconres', 'sconres', 'hres', 'sres'].index(st.session_state.analyze_bill_type),
            key="manual_bill_type"
        )
    
    with col2:
        congress = st.text_input(
            "Congress",
            value=st.session_state.analyze_congress,
            key="manual_congress"
        )
    
    with col3:
        bill_number = st.text_input(
            "Bill Number",
            value=st.session_state.analyze_bill_number,
            key="manual_bill_number"
        )
    
    # Update session state with current widget values
    st.session_state.analyze_bill_type = bill_type
    st.session_state.analyze_congress = congress
    st.session_state.analyze_bill_number = bill_number
    
    # Search/Analyze button - SINGLE INSTANCE ONLY
    analyze_button = st.button("Analyze Bill", type="primary", use_container_width=True, key="analyze_bill_main")
    
    # Only run analysis when button is clicked
    should_analyze = analyze_button and bill_type and congress and bill_number
    
    if should_analyze:
        
        with st.spinner("Fetching detailed bill data..."):
            # API endpoint
            url = f'https://api.congress.gov/v3/bill/{congress}/{bill_type}/{bill_number}'
            
            # Get API key from environment variable
            params = {
                'api_key': CONGRESS_API_KEY
            }
            
            # Make the API request
            response = requests.get(url, params=params)
            bill_data = response.json()
            
            if response.status_code == 200 and 'bill' in bill_data:
                # Extract key information from the bill data
                bill_info = bill_data['bill']
                
                # Display bill information
                st.header("Bill Information")
                
                st.subheader(bill_info['title'])
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**Bill Number:** {bill_info['type']} {bill_info['number']}")
                    st.markdown(f"**Congress:** {bill_info['congress']}")
                    st.markdown(f"**Introduced Date:** {bill_info['introducedDate']}")
                    if 'policyArea' in bill_info and bill_info['policyArea']:
                        st.markdown(f"**Policy Area:** {bill_info['policyArea']['name']}")
                    else:
                        st.markdown(f"**Policy Area:** Not yet assigned")
                
                with col2:
                    if 'sponsors' in bill_info and len(bill_info['sponsors']) > 0:
                        st.markdown(f"**Sponsor:** {bill_info['sponsors'][0]['fullName']} ({bill_info['sponsors'][0]['party']}-{bill_info['sponsors'][0]['state']})")
                    else:
                        st.markdown(f"**Sponsor:** Not available")
                    if 'cosponsors' in bill_info and 'count' in bill_info['cosponsors']:
                        st.markdown(f"**Cosponsors:** {bill_info['cosponsors']['count']}")
                    else:
                        st.markdown(f"**Cosponsors:** 0")
                    if 'actions' in bill_info and 'count' in bill_info['actions']:
                        st.markdown(f"**Total Actions:** {bill_info['actions']['count']}")
                    else:
                        st.markdown(f"**Total Actions:** 0")
                    if 'amendments' in bill_info and 'count' in bill_info['amendments']:
                        st.markdown(f"**Amendments:** {bill_info['amendments']['count']}")
                
                st.markdown("**Latest Action:**")
                if 'latestAction' in bill_info:
                    st.info(f"{bill_info['latestAction']['text']} (Date: {bill_info['latestAction']['actionDate']})")
                else:
                    st.info("No actions recorded yet")
                
                st.markdown("**Additional Information:**")
                if 'committeeReports' in bill_info:
                    st.write(f"- Committee Reports: {len(bill_info['committeeReports'])}")
                if 'relatedBills' in bill_info:
                    st.write(f"- Related Bills: {bill_info['relatedBills']['count']}")
                
                # Prepare a comprehensive text summary of the bill for OpenAI
                bill_text_for_analysis = f"""
Bill: {bill_info.get('title', 'Title not available')}
Bill Number: {bill_info.get('type', '')} {bill_info.get('number', '')}
Congress: {bill_info.get('congress', '')}
Introduced Date: {bill_info.get('introducedDate', 'Not available')}
"""
                
                if 'sponsors' in bill_info and len(bill_info['sponsors']) > 0:
                    bill_text_for_analysis += f"Sponsor: {bill_info['sponsors'][0]['fullName']} ({bill_info['sponsors'][0]['party']}-{bill_info['sponsors'][0]['state']})\n"
                
                if 'cosponsors' in bill_info and 'count' in bill_info['cosponsors']:
                    bill_text_for_analysis += f"Cosponsors: {bill_info['cosponsors']['count']}\n"
                
                if 'policyArea' in bill_info and bill_info['policyArea']:
                    bill_text_for_analysis += f"Policy Area: {bill_info['policyArea']['name']}\n"
                
                if 'latestAction' in bill_info:
                    bill_text_for_analysis += f"Latest Action: {bill_info['latestAction']['text']} (Date: {bill_info['latestAction']['actionDate']})\n"
                
                if 'constitutionalAuthorityStatementText' in bill_info and bill_info['constitutionalAuthorityStatementText']:
                    bill_text_for_analysis += f"\nConstitutional Authority:\n{bill_info['constitutionalAuthorityStatementText']}\n"
                
                bill_text_for_analysis += "\n\nAdditional Information:\n"
                
                if 'actions' in bill_info and 'count' in bill_info['actions']:
                    bill_text_for_analysis += f"- Total Actions: {bill_info['actions']['count']}\n"
                
                if 'amendments' in bill_info and 'count' in bill_info['amendments']:
                    bill_text_for_analysis += f"- Amendments: {bill_info['amendments']['count']}\n"
                
                if 'committeeReports' in bill_info and bill_info['committeeReports']:
                    bill_text_for_analysis += f"- Committee Reports: {len(bill_info['committeeReports'])}\n"
                
                if 'relatedBills' in bill_info and 'count' in bill_info['relatedBills']:
                    bill_text_for_analysis += f"- Related Bills: {bill_info['relatedBills']['count']}\n"
                
                # OpenAI Analysis
                st.header("AI-Powered Bill Analysis")
                
                with st.spinner("Analyzing bill with AI..."):
                    # Initialize OpenAI client with API key from .env
                    client = OpenAI(api_key=OPENAI_API_KEY)
                    
                    # Create the prompt for OpenAI
                    prompt = f"""
Please analyze the following congressional bill and provide:
1. A concise summary of what the bill does
2. Key pros (potential benefits)
3. Key cons (potential concerns or drawbacks)
4. Overall assessment

Bill Information:
{bill_text_for_analysis}
"""
                    
                    # Make the API call to OpenAI
                    response_ai = client.chat.completions.create(
                        model="gpt-4.1-nano",
                        messages=[
                            {"role": "system", "content": "You are a policy analyst expert who provides balanced, objective analysis of legislation."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.7,
                        max_tokens=1500
                    )
                    
                    # Extract the analysis
                    analysis = response_ai.choices[0].message.content
                    
                    st.markdown(analysis)
                
                # Legislative Journey & Floor Activity Section
                st.header("Legislative Journey & Floor Activity")
                
                with st.spinner("Fetching bill actions..."):
                    # Fetch bill actions
                    bill_actions_url = f'https://api.congress.gov/v3/bill/{congress}/{bill_type}/{bill_number}/actions'
                    
                    actions_params = {
                        'api_key': CONGRESS_API_KEY,
                        'limit': 250
                    }
                    
                    actions_response = requests.get(bill_actions_url, params=actions_params)
                    actions_data = actions_response.json()
                    
                    if actions_response.status_code == 200 and 'actions' in actions_data:
                        import pandas as pd
                        from datetime import datetime
                        
                        # Convert actions data to a DataFrame
                        actions_list = []
                        for action in actions_data['actions']:
                            action_dict = {
                                'date': action['actionDate'],
                                'text': action['text'],
                                'type': action.get('type', 'Unknown'),
                                'action_code': action.get('actionCode', ''),
                                'source_system': action.get('sourceSystem', {}).get('name', ''),
                                'action_time': action.get('actionTime', '')
                            }
                            
                            # Add committee info if available
                            if 'committees' in action and len(action['committees']) > 0:
                                action_dict['committee'] = action['committees'][0]['name']
                            else:
                                action_dict['committee'] = ''
                            
                            actions_list.append(action_dict)
                        
                        # Create DataFrame
                        actions_df = pd.DataFrame(actions_list)
                        actions_df['date'] = pd.to_datetime(actions_df['date'])
                        actions_df = actions_df.sort_values('date', ascending=False)
                        
                        # Summary Statistics
                        st.subheader("Summary Statistics")
                        
                        total_actions = len(actions_df)
                        floor_actions = len(actions_df[actions_df['type'] == 'Floor'])
                        committee_actions = len(actions_df[actions_df['type'] == 'Committee'])
                        days_since_intro = (datetime.now() - actions_df['date'].min()).days
                        
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric("Total Actions", total_actions)
                        with col2:
                            st.metric("Floor Actions", floor_actions)
                        with col3:
                            st.metric("Committee Actions", committee_actions)
                        with col4:
                            st.metric("Days Since Introduction", days_since_intro)
                        
                        # Timeline Visualization
                        st.subheader("Key Milestones Timeline")
                        
                        # Identify key milestones
                        milestones = []
                        
                        # Introduction
                        intro_actions = actions_df[actions_df['text'].str.contains('Introduced', case=False, na=False)]
                        if not intro_actions.empty:
                            milestones.append({
                                'date': intro_actions.iloc[-1]['date'],
                                'event': 'Introduction',
                                'description': intro_actions.iloc[-1]['text']
                            })
                        
                        # Committee actions
                        committee_referral = actions_df[actions_df['text'].str.contains('Referred to', case=False, na=False)]
                        if not committee_referral.empty:
                            milestones.append({
                                'date': committee_referral.iloc[-1]['date'],
                                'event': 'Committee Referral',
                                'description': committee_referral.iloc[-1]['text']
                            })
                        
                        # Floor votes
                        floor_votes = actions_df[actions_df['text'].str.contains('vote|passed|failed', case=False, na=False) & 
                                                 (actions_df['type'] == 'Floor')]
                        for _, vote in floor_votes.iterrows():
                            milestones.append({
                                'date': vote['date'],
                                'event': 'Floor Vote',
                                'description': vote['text']
                            })
                        
                        # Senate passage
                        senate_actions = actions_df[actions_df['text'].str.contains('Senate', case=False, na=False) & 
                                                    actions_df['text'].str.contains('passed|received', case=False, na=False)]
                        for _, senate in senate_actions.iterrows():
                            milestones.append({
                                'date': senate['date'],
                                'event': 'Senate Action',
                                'description': senate['text']
                            })
                        
                        # Create timeline DataFrame
                        if milestones:
                            timeline_df = pd.DataFrame(milestones)
                            timeline_df = timeline_df.sort_values('date')
                            
                            # Display timeline
                            for _, milestone in timeline_df.iterrows():
                                with st.container(border=True):
                                    col_date, col_event = st.columns([1, 3])
                                    with col_date:
                                        st.markdown(f"**{milestone['date'].strftime('%Y-%m-%d')}**")
                                    with col_event:
                                        st.markdown(f"**{milestone['event']}**")
                                        st.caption(milestone['description'])
                        else:
                            st.info("No key milestones identified yet.")
                        
                        # Interactive Actions Table
                        st.subheader("All Legislative Actions")
                        
                        # Display the dataframe
                        st.dataframe(
                            actions_df,
                            use_container_width=True,
                            hide_index=True,
                            column_config={
                                "date": st.column_config.DateColumn(
                                    "Date",
                                    format="YYYY-MM-DD"
                                ),
                                "text": st.column_config.TextColumn(
                                    "Action Description",
                                    width="large"
                                ),
                                "type": "Type",
                                "action_code": "Action Code",
                                "source_system": "Source System",
                                "action_time": "Time",
                                "committee": "Committee"
                            }
                        )
                        
                        st.caption(f"Showing {len(actions_df)} total actions")
                    else:
                        st.error("Failed to fetch bill actions data.")
                
            else:
                st.error("Failed to fetch bill data. Please check the bill number and try again.")
                st.json(bill_data)