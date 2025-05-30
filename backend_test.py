
import requests
import sys
import json
from datetime import datetime

class ActifyAPITester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.session = requests.Session()
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_group_id = "e4818c1d-9547-4bb9-8d65-62ab55ef9515"  # Test group ID from request
        self.test_user_id = "967c04e7-47ae-487d-8226-183d390c7808"  # Test user ID from request

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None, form_data=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'} if not form_data and not files else {}
        
        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = self.session.get(url, headers=headers)
            elif method == 'POST':
                if form_data:
                    response = self.session.post(url, data=form_data, files=files)
                else:
                    response = self.session.post(url, json=data, headers=headers)
            
            success = response.status_code == expected_status
            
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return success, response.json()
                except:
                    return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    print(f"Response: {response.text}")
                    return False, response.json()
                except:
                    return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_login(self, username, password):
        """Test login functionality"""
        success, response = self.run_test(
            "Login",
            "POST",
            "login",
            200,
            data={"username": username, "password": password}
        )
        
        if success and 'user' in response:
            self.user_id = response['user']['id']
            print(f"Logged in as user: {response['user']['username']} (ID: {self.user_id})")
            return True
        return False

    def test_get_user_groups(self):
        """Test getting user's groups"""
        success, response = self.run_test(
            "Get User Groups",
            "GET",
            f"users/{self.test_user_id}/groups",
            200
        )
        
        if success:
            print(f"Found {len(response)} groups for user")
            if len(response) > 0:
                print(f"First group: {response[0]['name']} (ID: {response[0]['id']})")
                # Check if our test group is in the list
                test_group = next((g for g in response if g['id'] == self.test_group_id), None)
                if test_group:
                    print(f"Found test group: {test_group['name']} (ID: {test_group['id']})")
                    print(f"Group status: {test_group['activities_submitted_this_week']}/7 activities submitted")
                    print(f"Submission phase active: {test_group['submission_phase_active']}")
                    return True
                else:
                    print("Test group not found in user's groups")
            return len(response) > 0
        return False

    def test_get_group_details(self):
        """Test getting group details"""
        success, response = self.run_test(
            "Get Group Details",
            "GET",
            f"groups/{self.test_group_id}",
            200
        )
        
        if success:
            print(f"Group name: {response['name']}")
            print(f"Member count: {response['member_count']}/{response['max_members']}")
            print(f"Activities submitted: {response['activities_submitted_this_week']}/7")
            print(f"Submission phase active: {response['submission_phase_active']}")
            return True
        return False

    def test_get_weekly_activities(self):
        """Test getting weekly activities for a group"""
        success, response = self.run_test(
            "Get Weekly Activities",
            "GET",
            f"groups/{self.test_group_id}/weekly-activities",
            200
        )
        
        if success:
            print(f"Found {len(response)} weekly activities")
            if len(response) > 0:
                for idx, activity in enumerate(response):
                    print(f"Activity {idx+1}: {activity['activity_title']}")
                    print(f"  Revealed: {activity['is_revealed']}")
            return True
        return False

    def test_get_current_day_activity(self):
        """Test getting current day's activity"""
        success, response = self.run_test(
            "Get Current Day Activity",
            "GET",
            f"groups/{self.test_group_id}/current-day-activity",
            200
        )
        
        if success:
            if response.get('activity'):
                print(f"Current day activity: {response['activity'].get('activity_title', 'No title')}")
                print(f"Description: {response['activity'].get('activity_description', 'No description')}")
                print(f"Revealed at: {response['activity'].get('revealed_at', 'Unknown')}")
                return True
            else:
                print("No current day activity found")
                return False
        return False

    def test_reveal_daily_activity(self):
        """Test revealing daily activity (admin function)"""
        form_data = {
            'admin_id': self.test_user_id,
            'day_number': 2  # Reveal day 2 activity
        }
        
        success, response = self.run_test(
            "Reveal Daily Activity",
            "POST",
            f"groups/{self.test_group_id}/reveal-daily-activity",
            200,
            form_data=form_data
        )
        
        if success:
            print(f"Response: {response}")
            if response.get('success'):
                print(f"Revealed activity: {response['revealed_activity']['activity_title']}")
                print(f"Day number: {response['day_number']}")
                return True
            else:
                print(f"Failed to reveal activity: {response.get('message', 'Unknown error')}")
                return False
        return False

    def test_weekly_rankings(self):
        """Test getting weekly rankings"""
        success, response = self.run_test(
            "Get Weekly Rankings",
            "GET",
            f"groups/{self.test_group_id}/weekly-rankings",
            200
        )
        
        if success:
            if 'rankings' in response:
                print(f"Found {len(response['rankings'])} members in rankings")
                for idx, member in enumerate(response['rankings']):
                    print(f"Rank {idx+1}: {member.get('username', 'Unknown')} - {member.get('points', 0)} points")
                return True
            else:
                print("No rankings found in response")
                return False
        return False

def main():
    # Get the backend URL from environment variable
    backend_url = "https://333114a3-9b04-4aaa-a7b1-93d53ba2d24b.preview.emergentagent.com/api"
    
    # Setup tester
    tester = ActifyAPITester(backend_url)
    
    # Run tests
    print("\n🚀 Starting ACTIFY API Tests...\n")
    
    # Test login
    if not tester.test_login("testuser", "password123"):
        print("❌ Login failed, stopping tests")
        return 1
    
    # Test getting user's groups
    tester.test_get_user_groups()
    
    # Test getting group details
    tester.test_get_group_details()
    
    # Test getting weekly activities
    tester.test_get_weekly_activities()
    
    # Test getting current day activity
    tester.test_get_current_day_activity()
    
    # Test revealing daily activity (admin function)
    tester.test_reveal_daily_activity()
    
    # Test weekly rankings
    tester.test_weekly_rankings()
    
    # Print results
    print(f"\n📊 Tests passed: {tester.tests_passed}/{tester.tests_run}")
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())
