from django.shortcuts import render
import requests
import os
import json
from dotenv import load_dotenv
import urllib.parse

# Load environment variables from .env file
load_dotenv()

def get_salesforce_token():
    """Obtain OAuth token from Salesforce"""
    try:
        # Get credentials from environment variables
        consumer_key = os.getenv('CONSUMER_KEY')
        consumer_secret = os.getenv('CONSUMER_SECRET')
        username = os.getenv('USERNAME')
        password = os.getenv('PASSWORD')
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
    
    return render(request, 'sf_connection_test/sf-connection-test.html', context)

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
    
    return render(request, 'sf_connection_test/sf-affiliation-query.html', context)
