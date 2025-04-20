from django.shortcuts import render
import requests
import os
import json
from dotenv import load_dotenv
import urllib.parse
from django.http import JsonResponse

# Load environment variables from .env file
load_dotenv()

def get_salesforce_token():
    """Obtain OAuth token from Salesforce"""
    try:
        # Get credentials from environment variables
        consumer_key = os.getenv('CONSUMER_KEY')
        consumer_secret = os.getenv('CONSUMER_SECRET')
        username = os.getenv('SF_USERNAME')
        password = os.getenv('SF_PASSWORD')
        sf_domain = os.getenv('SF_DOMAIN')
        
        # Check if required credentials are provided
        if not all([consumer_key, consumer_secret, username, password, sf_domain]):
            return {
                'success': False,
                'error': 'Missing Salesforce credentials in .env file'
            }
        
        # Construct the OAuth token request
        # Use the sf_domain as the base URL
        token_url = f"{sf_domain}/services/oauth2/token"
        payload = {
            'grant_type': 'password',
            'client_id': consumer_key,
            'client_secret': consumer_secret,
            'username': username,
            'password': password
        }
        
        # Make the OAuth request
        response = requests.post(token_url, data=payload)
        response_data = response.json()
        
        if response.status_code == 200:
            return {
                'success': True,
                'access_token': response_data['access_token'],
                'instance_url': response_data['instance_url']
            }
        else:
            return {
                'success': False,
                'error': response_data.get('error_description', 'Unknown error'),
                'details': response_data
            }
    except Exception as e:
        return {
            'success': False,
            'error': f'Exception occurred: {str(e)}'
        }

def test_salesforce_connection(request):
    """View to test Salesforce connection and display results"""
    # Get Salesforce connection token
    token_result = get_salesforce_token()
    
    # Check if token request was successful
    if token_result['success']:
        # Try to fetch some basic information from Salesforce API
        try:
            headers = {
                'Authorization': f'Bearer {token_result["access_token"]}',
                'Content-Type': 'application/json'
            }
            
            # Get current Salesforce user info
            user_info_url = f"{token_result['instance_url']}/services/data/v58.0/chatter/users/me"
            user_response = requests.get(user_info_url, headers=headers)
            
            if user_response.status_code == 200:
                user_data = user_response.json()
                context = {
                    'connection_successful': True,
                    'user_info': user_data,
                    'instance_url': token_result['instance_url']
                }
            else:
                # Token was created but API request failed
                context = {
                    'connection_successful': False,
                    'error': f"API Request Failed: {user_response.status_code}",
                    'details': user_response.json() if user_response.text else 'No details provided'
                }
        except Exception as e:
            context = {
                'connection_successful': False,
                'error': f'API Request Exception: {str(e)}'
            }
    else:
        # Token creation failed
        context = {
            'connection_successful': False,
            'error': token_result['error'],
            'details': token_result.get('details', {})
        }
    
    return render(request, 'connection_tests/sf-connection-test.html', context)

def query_salesforce_affiliations(request):
    """View to query Salesforce for active Endeavor staff affiliations"""
    # Get Salesforce connection token
    token_result = get_salesforce_token()
    
    # Define the specific fields query - we're no longer using FIELDS(All)
    specific_fields_query = """
        SELECT npe5__StartDate__c, npe5__EndDate__c, Contact_Name__c, Email_Address__c, 
        Endeavor_Team__c, Position_Level_at_Endeavor__c, Account_Name__c
        FROM npe5__Affiliation__c 
        WHERE Affiliation_Summary__c = 'Active Endeavor Staff'
    """
    
    # Prepare context for the template
    context = {
        'title': 'Salesforce Affiliation Query',
        'query': specific_fields_query
    }
    
    # Check if token request was successful
    if token_result['success']:
        try:
            headers = {
                'Authorization': f'Bearer {token_result["access_token"]}',
                'Content-Type': 'application/json'
            }
            
            # Make a single query with specific fields (no more pagination needed)
            encoded_query = urllib.parse.quote(specific_fields_query, safe='')
            query_url = f"{token_result['instance_url']}/services/data/v58.0/query/?q={encoded_query}"
            
            # Make the query request
            response = requests.get(query_url, headers=headers)
            
            if response.status_code == 200:
                query_data = response.json()
                records = query_data.get('records', [])
                
                # Add query results to context
                context.update({
                    'query_successful': True,
                    'total_records': query_data.get('totalSize', 0),
                    'records': records,
                    'instance_url': token_result['instance_url']
                })
            else:
                # Query failed
                context.update({
                    'query_successful': False,
                    'error': f"API Query Failed: {response.status_code}",
                    'details': response.json() if response.text else 'No details provided'
                })
        except Exception as e:
            context.update({
                'query_successful': False,
                'error': f'API Request Exception: {str(e)}'
            })
    else:
        # Token creation failed
        context.update({
            'query_successful': False,
            'error': token_result['error'],
            'details': token_result.get('details', {})
        })
    
    return render(request, 'connection_tests/sf-affiliation-query.html', context)

def dashworks_chat(request):
    """View to provide a chat interface with DashWorks AI"""
    # Create context with default values
    context = {
        'title': 'DashWorks AI Chat',
        'chat_initialized': True,
        'messages': [],
    }
    
    # Get DashWorks API key from environment variables
    dashworks_key = os.getenv('DASHWORKS_KEY')
    
    if not dashworks_key:
        context.update({
            'chat_initialized': False,
            'error': 'Missing DashWorks API key in .env file'
        })
        return render(request, 'connection_tests/dashworks-chat.html', context)
    
    # Handle clear chat request
    if request.method == 'POST' and 'clear_chat' in request.POST:
        print("Clearing chat history")
        if 'chat_messages' in request.session:
            del request.session['chat_messages']
        return render(request, 'connection_tests/dashworks-chat.html', context)
    
    # Load existing messages from session
    messages = request.session.get('chat_messages', [])
    
    # Handle chat message submission
    if request.method == 'POST' and 'message' in request.POST:
        user_message = request.POST.get('message')
        
        # Get the selected bot_id and bot_name from the form
        bot_id = request.POST.get('bot_id', 'bbbfd13602d44901a75c59d09ed235d7')  # Default to Company_Profile
        bot_name = request.POST.get('bot_name', 'Company_Profile')  # Default name
        
        print(f"User message: {user_message} (using bot: {bot_name}, ID: {bot_id})")
        
        # Add user message to chat history
        messages.append({'role': 'user', 'content': user_message})
        
        # Save session immediately after adding user message
        request.session['chat_messages'] = messages
        request.session.modified = True
        
        try:
            # Prepare API request            
            response = requests.post(
                "https://api.dashworks.ai/v1/answer",
                headers={
                    "Authorization": f"Bearer {dashworks_key.strip()}",
                    "Content-Type": "application/json"
                },
                json={
                    "message": user_message,
                    "bot_id": bot_id,
                    "inline_sources": True,
                    "stream": False
                }
            )
            
            print(f"API response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                ai_response = data.get('answer', 'No response from AI')
                sources = data.get('sources', [])
                
                # Add AI response to chat history
                messages.append({'role': 'assistant', 'content': ai_response, 'sources': sources})
            else:
                error_message = f"DashWorks API Error: {response.status_code}"
                messages.append({'role': 'system', 'content': error_message})
                context['error'] = error_message
                
                try:
                    error_details = response.json()
                    context['details'] = error_details
                except:
                    context['details'] = response.text if response.text else "No error details available"
                
        except Exception as e:
            error_message = f'API Request Exception: {str(e)}'
            messages.append({'role': 'system', 'content': error_message})
            context['error'] = error_message
        
        # Save updated messages to session
        request.session['chat_messages'] = messages
        request.session.modified = True
    
    # Add messages to context
    context['messages'] = messages
    
    return render(request, 'connection_tests/dashworks-chat.html', context)

def test_dashworks_api(request):
    """Simple view to test DashWorks API connection"""
    context = {
        'title': 'DashWorks API Test',
    }
    
    # Get DashWorks API key from environment variables
    dashworks_key = os.getenv('DASHWORKS_KEY')
    
    if not dashworks_key:
        context.update({
            'success': False,
            'error': 'Missing DashWorks API key in .env file'
        })
        return render(request, 'connection_tests/api-test.html', context)
    
    # Only proceed if the user clicked the test button
    if request.method == 'POST':
        try:
            # Try different authorization methods
            test_results = []
            
            # Test 1: Raw API key
            response1 = requests.post(
                "https://api.dashworks.ai/v1/answer",
                headers={
                    "Authorization": dashworks_key,
                    "Content-Type": "application/json"
                },
                json={
                    "message": "Hello, this is a test message",
                    "bot_id": "480f108b1d1041b28ff8af5d3be95276",
                    "inline_sources": True,
                    "stream": False
                }
            )
            test_results.append({
                'method': 'Raw API key',
                'status': response1.status_code,
                'headers_sent': {"Authorization": dashworks_key[:5] + '...' + dashworks_key[-5:]},
                'response': response1.text[:100] + '...' if len(response1.text) > 100 else response1.text
            })
            
            # Test 2: Bearer prefix
            response2 = requests.post(
                "https://api.dashworks.ai/v1/answer",
                headers={
                    "Authorization": f"Bearer {dashworks_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "message": "Hello, this is a test message",
                    "bot_id": "480f108b1d1041b28ff8af5d3be95276",
                    "inline_sources": True,
                    "stream": False
                }
            )
            test_results.append({
                'method': 'Bearer prefix',
                'status': response2.status_code,
                'headers_sent': {"Authorization": f"Bearer {dashworks_key[:5]}...{dashworks_key[-5:]}"},
                'response': response2.text[:100] + '...' if len(response2.text) > 100 else response2.text
            })
            
            # Test 3: Lowercase authorization
            response3 = requests.post(
                "https://api.dashworks.ai/v1/answer",
                headers={
                    "authorization": dashworks_key,
                    "Content-Type": "application/json"
                },
                json={
                    "message": "Hello, this is a test message",
                    "bot_id": "480f108b1d1041b28ff8af5d3be95276",
                    "inline_sources": True,
                    "stream": False
                }
            )
            test_results.append({
                'method': 'Lowercase authorization',
                'status': response3.status_code,
                'headers_sent': {"authorization": dashworks_key[:5] + '...' + dashworks_key[-5:]},
                'response': response3.text[:100] + '...' if len(response3.text) > 100 else response3.text
            })
            
            context.update({
                'success': True,
                'test_results': test_results
            })
            
        except Exception as e:
            context.update({
                'success': False,
                'error': f'API Request Exception: {str(e)}'
            })
    
    return render(request, 'connection_tests/api-test.html', context)

def debug_info(request):
    """View to display debug information"""
    debug_data = {
        'session_keys': list(request.session.keys()),
        'dashworks_key_set': bool(os.getenv('DASHWORKS_KEY')),
        'dashworks_key_length': len(os.getenv('DASHWORKS_KEY', '')),
        'request_method': request.method,
        'cookies': request.COOKIES,
    }
    
    # If chat messages exist in the session, show a preview
    if 'chat_messages' in request.session:
        messages = request.session['chat_messages']
        debug_data['messages_count'] = len(messages)
        if messages:
            debug_data['last_message'] = {
                'role': messages[-1]['role'],
                'content_preview': messages[-1]['content'][:50] + '...' if len(messages[-1]['content']) > 50 else messages[-1]['content']
            }
    
    return render(request, 'connection_tests/debug-info.html', {'debug_data': debug_data})

def curl_test(request):
    """A view that shows curl-like commands to test the API directly"""
    dashworks_key = os.getenv('DASHWORKS_KEY', 'YOUR_API_KEY')
    bot_id = "480f108b1d1041b28ff8af5d3be95276"
    
    # Generate commands for testing
    curl_commands = [
        {
            'title': 'Test with Bearer prefix',
            'command': f'curl -X POST https://api.dashworks.ai/v1/answer \\\n'
                      f'  -H "Authorization: Bearer {dashworks_key}" \\\n'
                      f'  -H "Content-Type: application/json" \\\n'
                      f'  -d \'{{"message": "Hello", "bot_id": "{bot_id}", "inline_sources": true, "stream": false}}\''
        },
        {
            'title': 'Test with raw API key',
            'command': f'curl -X POST https://api.dashworks.ai/v1/answer \\\n'
                      f'  -H "Authorization: {dashworks_key}" \\\n'
                      f'  -H "Content-Type: application/json" \\\n'
                      f'  -d \'{{"message": "Hello", "bot_id": "{bot_id}", "inline_sources": true, "stream": false}}\''
        },
        {
            'title': 'Test with Python requests',
            'command': f'import requests\n\n'
                      f'response = requests.post(\n'
                      f'    "https://api.dashworks.ai/v1/answer",\n'
                      f'    headers={{\n'
                      f'        "Authorization": "Bearer {dashworks_key}",\n'
                      f'        "Content-Type": "application/json"\n'
                      f'    }},\n'
                      f'    json={{\n'
                      f'        "message": "Hello",\n'
                      f'        "bot_id": "{bot_id}",\n'
                      f'        "inline_sources": True,\n'
                      f'        "stream": False\n'
                      f'    }}\n'
                      f')\n\n'
                      f'print(response.status_code)\n'
                      f'print(response.text)'
        }
    ]
    
    context = {
        'title': 'API Testing Commands',
        'curl_commands': curl_commands,
        'api_key': f"{dashworks_key[:5]}...{dashworks_key[-5:]}",
        'bot_id': bot_id
    }
    
    return render(request, 'connection_tests/curl-test.html', context)

# Notion Dashboard Views
def notion_dashboard(request):
    """
    Render the Notion dashboard page.
    """
    return render(request, "connection_tests/notion/notion-dashboard.html")

def get_notion_database():
    """
    Fetch the database from Notion with pagination support.
    Handles retrieving all pages even when there are more than 100 pages.
    """
    # Load environment variables
    NOTION_TOKEN = os.getenv("NOTION_TOKEN")
    DATABASE_ID = "1cbbd9fe4dd680b6a1d8cc680254bc88"
    
    headers = {
        "Authorization": "Bearer " + NOTION_TOKEN,
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }
    
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
    pages_data = get_notion_database()
    
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
