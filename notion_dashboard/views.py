from django.shortcuts import render
import requests
from datetime import datetime, timezone
import json
import os
from dotenv import load_dotenv
from django.http import JsonResponse

# Load environment variables from .env file
load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = "1cbbd9fe4dd680b6a1d8cc680254bc88"


# Create your views here.
def notion_dashboard(request):
    """
    Render the Notion dashboard page.
    """
    return render(request, "notion_dashboard/notion-dashboard.html")

headers = {
    "Authorization": "Bearer " + NOTION_TOKEN,
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}

def get_database():
    """
    Fetch the database from Notion with pagination support.
    Handles retrieving all pages even when there are more than 100 pages.
    """
    all_results = []
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    has_more = True
    next_cursor = None
    
    while has_more:
        # Prepare request body with pagination cursor if available
        body = {}
        if next_cursor:
            body["start_cursor"] = next_cursor
            
        # Make the API request
        response = requests.post(url, headers=headers, json=body)
        
        if response.status_code == 200:
            data = response.json()
            
            # Add current batch of results to the full list
            if 'results' in data:
                all_results.extend(data['results'])
                
            # Check if there are more pages to fetch
            has_more = data.get('has_more', False)
            next_cursor = data.get('next_cursor')
            
            # If we've processed all pages, break the loop
            if not has_more or not next_cursor:
                break
                
            print(f"Fetched batch of pages. Total so far: {len(all_results)}")
        else:
            print(f"Error: {response.status_code}, {response.text}")
            return None
    
    # Compile all results into a single response format
    complete_response = {
        "object": "list",
        "results": all_results,
        "has_more": False,
        "next_cursor": None
    }
    
    # Save the complete response to a JSON file
    filename = "notion_database.json"
    with open(filename, 'w') as f:
        json.dump(complete_response, f, indent=4)
    print(f"Database data saved to {filename} (Total: {len(all_results)} pages)")
    
    return complete_response

def fetch_notion_data(request):
    """
    API endpoint to fetch Notion database data and return as JSON for the dashboard
    """
    pages_data = get_database()
    
    if not pages_data or 'results' not in pages_data:
        return JsonResponse({
            'success': False,
            'error': 'Failed to fetch data from Notion'
        })
    
    # Process the results into a more frontend-friendly format
    processed_pages = []
    
    for page in pages_data['results']:
        properties = page.get('properties', {})
        
        # Create a dictionary with all the data we need for the table
        processed_page = {
            'id': page.get('id'),
            'url': page.get('url'),
            'username': properties.get('username', {}).get('title', [{}])[0].get('plain_text', 'N/A'),
            'first_name': properties.get('firstName', {}).get('rich_text', [{}])[0].get('plain_text', 'N/A'),
            'last_name': properties.get('lastName', {}).get('rich_text', [{}])[0].get('plain_text', 'N/A'),
            'email': properties.get('primaryEmail', {}).get('email', 'N/A'),
            'title': properties.get('title', {}).get('rich_text', [{}])[0].get('plain_text', 'N/A'),
            'department': properties.get('department', {}).get('rich_text', [{}])[0].get('plain_text', 'N/A'),
            'endeavor_office': properties.get('endeavorOffice', {}).get('rich_text', [{}])[0].get('plain_text', 'N/A'),
            'position_level': properties.get('positionLevelAtEndeavor', {}).get('rich_text', [{}])[0].get('plain_text', 'N/A'),
            'affiliation_id': properties.get('affiliationId', {}).get('rich_text', [{}])[0].get('plain_text', 'N/A'),
            'start_date': properties.get('startDate', {}).get('date', {}).get('start', 'N/A'),
            'end_date': properties.get('endDate', {}).get('date', {}).get('start', 'N/A'),
        }
        
        processed_pages.append(processed_page)
    
    return JsonResponse({
        'success': True,
        'pages': processed_pages,
        'total_count': len(processed_pages)
    })

pages_data = get_database()
if pages_data and 'results' in pages_data:
    for page in pages_data['results']:
        # Extract page ID and url
        page_id = page.get('id')
        page_url = page.get('url')
        
        # Access properties
        properties = page.get('properties', {})
        
        # Extract common fields
        username = properties.get('username', {}).get('title', [{}])[0].get('plain_text', 'N/A')
        first_name = properties.get('firstName', {}).get('rich_text', [{}])[0].get('plain_text', 'N/A')
        last_name = properties.get('lastName', {}).get('rich_text', [{}])[0].get('plain_text', 'N/A')
        email = properties.get('primaryEmail', {}).get('email', 'N/A')
        title = properties.get('title', {}).get('rich_text', [{}])[0].get('plain_text', 'N/A')
        department = properties.get('department', {}).get('rich_text', [{}])[0].get('plain_text', 'N/A')
        
        # Add missing fields
        endeavor_office = properties.get('endeavorOffice', {}).get('rich_text', [{}])[0].get('plain_text', 'N/A')
        position_level = properties.get('positionLevelAtEndeavor', {}).get('rich_text', [{}])[0].get('plain_text', 'N/A')
        affiliation_id = properties.get('affiliationId', {}).get('rich_text', [{}])[0].get('plain_text', 'N/A')
        
        # Get dates if available
        start_date = properties.get('startDate', {}).get('date', {}).get('start', 'N/A')
        end_date = properties.get('endDate', {}).get('date', {}).get('start', 'N/A')
        
        # Print extracted information
        print(f"Page ID: {page_id}")
        print(f"Username: {username}")
        print(f"First Name: {first_name}")
        print(f"Last Name: {last_name}")
        print(f"Email: {email}")
        print(f"Title: {title}")
        print(f"Department: {department}")
        print(f"Endeavor Office: {endeavor_office}")
        print(f"Position Level: {position_level}")
        print(f"Affiliation ID: {affiliation_id}")
        print(f"Start Date: {start_date}")
        print(f"End Date: {end_date}")
        print(f"URL: {page_url}")
        print("-" * 50)
else:
    print("No pages found in the database response")



