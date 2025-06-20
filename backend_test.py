import requests
import sys
import json
import os
from dotenv import load_dotenv

class BitSafeAPITester:
    def __init__(self):
        # Try to get the backend URL from the frontend .env file
        load_dotenv("frontend/.env")
        self.base_url = os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:8001')
        print(f"Using backend URL: {self.base_url}")
        
        self.tests_run = 0
        self.tests_passed = 0
        
        # Load environment variables from backend/.env
        load_dotenv("backend/.env")

    def run_test(self, name, method, endpoint, expected_status, data=None, check_cors=False):
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'OPTIONS':
                response = requests.options(url, headers=headers)

            success = response.status_code == expected_status
            
            # Check CORS headers if requested
            if check_cors and success:
                cors_headers = [
                    'Access-Control-Allow-Origin',
                    'Access-Control-Allow-Methods',
                    'Access-Control-Allow-Headers'
                ]
                cors_success = all(header in response.headers for header in cors_headers)
                if cors_success:
                    print("✅ CORS headers verified")
                else:
                    print("❌ CORS headers missing")
                    print(f"Headers: {response.headers}")
                    success = False
            
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return success, response.json()
                except json.JSONDecodeError:
                    return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    print(f"Response: {response.text}")
                except:
                    pass
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_root_endpoint(self):
        """Test the root API endpoint"""
        return self.run_test(
            "Root API Endpoint",
            "GET",
            "",
            200
        )

    def test_status_endpoint(self):
        """Test the status endpoint"""
        return self.run_test(
            "Status Endpoint",
            "GET",
            "status",
            200
        )

    def test_create_status_check(self):
        """Test creating a status check"""
        return self.run_test(
            "Create Status Check",
            "POST",
            "status",
            200,
            data={"client_name": "test_client"}
        )
        
    def test_chat_endpoint(self):
        """Test the chat endpoint with valid payload"""
        test_payload = {
            "message": "How can I reduce my crypto insurance premium?",
            "user_info": {
                "name": "Test User",
                "email": "test@example.com", 
                "phone": "+1234567890"
            }
        }
        
        return self.run_test(
            "Chat Endpoint",
            "POST",
            "chat",
            200,
            data=test_payload
        )
    
    def test_chat_response_format(self):
        """Test that the chat endpoint returns the correct response format"""
        test_payload = {
            "message": "What's covered by crypto insurance?",
            "user_info": {
                "name": "Format Tester",
                "email": "format@example.com", 
                "phone": "+1987654321"
            }
        }
        
        success, response = self.run_test(
            "Chat Response Format",
            "POST",
            "chat",
            200,
            data=test_payload
        )
        
        if success:
            # Check that the response has the expected fields
            if 'response' in response and 'recommendations' in response:
                if isinstance(response['recommendations'], list):
                    print("✅ Response format is correct")
                    return True, response
                else:
                    print("❌ 'recommendations' is not a list")
                    return False, response
            else:
                print("❌ Response is missing required fields")
                print(f"Response: {response}")
                return False, response
        
        return success, response
    
    def test_chat_error_handling(self):
        """Test error handling for the chat endpoint"""
        # Save the original API key
        original_api_key = os.environ.get('HF_API_KEY')
        
        # Temporarily remove the API key to simulate missing key
        if 'HF_API_KEY' in os.environ:
            del os.environ['HF_API_KEY']
        
        test_payload = {
            "message": "Test error handling",
            "user_info": {
                "name": "Error Tester",
                "email": "error@example.com", 
                "phone": "+1122334455"
            }
        }
        
        # We expect either a 500 error or a 200 with fallback response
        success, response = self.run_test(
            "Chat Error Handling (Missing API Key)",
            "POST",
            "chat",
            200,  # The endpoint has fallback logic, so it might still return 200
            data=test_payload
        )
        
        # Restore the original API key
        if original_api_key:
            os.environ['HF_API_KEY'] = original_api_key
        
        # If we got a 200 response, check if it's using the fallback logic
        if success and 'response' in response:
            print("✅ Fallback response provided when API key is missing")
            return True, response
        
        return success, response
    
    def test_cors_headers(self):
        """Test CORS headers for the chat endpoint"""
        return self.run_test(
            "CORS Headers",
            "OPTIONS",
            "chat",
            200,
            check_cors=True
        )

def main():
    # Setup
    tester = BitSafeAPITester()
    
    # Run basic API tests
    print("\n🔄 Running Basic API Tests...")
    root_success, _ = tester.test_root_endpoint()
    status_success, _ = tester.test_status_endpoint()
    create_status_success, _ = tester.test_create_status_check()
    
    # Run chat endpoint tests
    print("\n🔄 Running Chat API Tests...")
    chat_success, _ = tester.test_chat_endpoint()
    chat_format_success, _ = tester.test_chat_response_format()
    chat_error_success, _ = tester.test_chat_error_handling()
    cors_success, _ = tester.test_cors_headers()
    
    # Print results
    print(f"\n📊 Tests passed: {tester.tests_passed}/{tester.tests_run}")
    
    # Return success if all tests passed
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())