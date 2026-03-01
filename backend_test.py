#!/usr/bin/env python3
"""
Comprehensive backend testing for Dubai Travel Assistant API.
Tests the Google ADK migration and all endpoints.
"""

import asyncio
import aiohttp
import json
import os
import uuid
import time
from datetime import datetime

# Backend URL: set BACKEND_URL env or default to local
BASE_URL = os.environ.get("BACKEND_URL", "http://localhost:8000").rstrip("/") + "/api"

class DubaiTravelAssistantTests:
    def __init__(self):
        self.session_id = str(uuid.uuid4())
        self.results = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "errors": []
        }

    async def run_all_tests(self):
        """Run all backend tests in sequence."""
        print("=" * 80)
        print("DUBAI TRAVEL ASSISTANT - BACKEND API TESTS")
        print("Testing Google ADK Migration")
        print("=" * 80)
        
        async with aiohttp.ClientSession() as session:
            self.session = session
            
            # Health Check
            await self.test_health_endpoint()
            
            # Activity Endpoints
            await self.test_list_activities()
            await self.test_get_single_activity()
            await self.test_get_invalid_activity()
            
            # Chat Endpoints (Core Google ADK functionality)
            await self.test_chat_greeting()
            await self.test_chat_activity_query()
            await self.test_chat_activity_listing()
            await self.test_chat_escalation()
            await self.test_chat_booking_flow()
            
            # Conversation History
            await self.test_conversation_history()
            
            # Bookings
            await self.test_get_bookings()
            
            # Supervisor Reply
            await self.test_supervisor_reply()
        
        self.print_summary()

    async def make_request(self, method, endpoint, data=None, expected_status=200):
        """Make HTTP request and handle errors."""
        self.results["total_tests"] += 1
        url = f"{BASE_URL}{endpoint}"
        
        try:
            if method == "GET":
                async with self.session.get(url) as response:
                    status = response.status
                    text = await response.text()
            elif method == "POST":
                headers = {"Content-Type": "application/json"}
                async with self.session.post(url, data=json.dumps(data), headers=headers) as response:
                    status = response.status
                    text = await response.text()
            
            if status != expected_status:
                self.results["failed"] += 1
                error = f"Expected status {expected_status}, got {status}. Response: {text[:200]}"
                self.results["errors"].append(error)
                return None, error
            
            try:
                response_data = json.loads(text)
                self.results["passed"] += 1
                return response_data, None
            except json.JSONDecodeError:
                if expected_status == 200:  # Only expect JSON for 200 responses
                    self.results["failed"] += 1
                    error = f"Invalid JSON response: {text[:200]}"
                    self.results["errors"].append(error)
                    return None, error
                else:
                    self.results["passed"] += 1
                    return {"raw_text": text}, None
                    
        except Exception as e:
            self.results["failed"] += 1
            error = f"Request failed: {str(e)}"
            self.results["errors"].append(error)
            return None, error

    # ===============================
    # HEALTH & ACTIVITY TESTS
    # ===============================

    async def test_health_endpoint(self):
        """Test GET /api/health"""
        print("\n🔍 Testing Health Endpoint...")
        
        response, error = await self.make_request("GET", "/health")
        if error:
            print(f"❌ Health check failed: {error}")
            return
            
        if response.get("status") == "healthy":
            print("✅ Health endpoint working")
        else:
            print(f"❌ Health endpoint returned unexpected response: {response}")

    async def test_list_activities(self):
        """Test GET /api/activities - should return 12 activities"""
        print("\n🔍 Testing List Activities...")
        
        response, error = await self.make_request("GET", "/activities")
        if error:
            print(f"❌ List activities failed: {error}")
            return
            
        activities = response.get("activities", [])
        if len(activities) == 12:
            print(f"✅ List activities returned {len(activities)} activities")
            # Check if activities have required fields
            sample = activities[0]
            required_fields = ["id", "name", "description", "image", "category", "available", "price_from", "currency"]
            for field in required_fields:
                if field not in sample:
                    print(f"❌ Missing field '{field}' in activity")
                    return
            print("✅ All activities have required fields")
        else:
            print(f"❌ Expected 12 activities, got {len(activities)}")

    async def test_get_single_activity(self):
        """Test GET /api/activities/{activity_id} for valid activity"""
        print("\n🔍 Testing Single Activity (burj-khalifa)...")
        
        response, error = await self.make_request("GET", "/activities/burj-khalifa")
        if error:
            print(f"❌ Get single activity failed: {error}")
            return
            
        activity = response.get("activity")
        if activity and activity.get("id") == "burj-khalifa":
            print("✅ Single activity endpoint working")
            # Check for detailed activity fields
            required_fields = ["variations", "cancellation_policy", "reschedule_policy"]
            for field in required_fields:
                if field not in activity:
                    print(f"❌ Missing detailed field '{field}' in activity")
                    return
            print("✅ Activity has all detailed fields")
        else:
            print(f"❌ Invalid activity response: {activity}")

    async def test_get_invalid_activity(self):
        """Test GET /api/activities/{activity_id} for invalid activity"""
        print("\n🔍 Testing Invalid Activity ID...")
        
        response, error = await self.make_request("GET", "/activities/invalid-activity", expected_status=404)
        if error:
            print(f"❌ Invalid activity test failed: {error}")
            return
            
        print("✅ Invalid activity correctly returns 404")

    # ===============================
    # CHAT TESTS (Google ADK Core)
    # ===============================

    async def test_chat_greeting(self):
        """Test POST /api/chat with greeting message"""
        print("\n🔍 Testing Chat - Greeting Message...")
        
        data = {
            "session_id": self.session_id,
            "message": "Hello! I'm interested in Dubai activities."
        }
        
        response, error = await self.make_request("POST", "/chat", data)
        if error:
            print(f"❌ Chat greeting failed: {error}")
            return
            
        if response.get("status") == "ok" and "response" in response:
            chat_response = response["response"]
            if chat_response.get("type") == "text" and "message" in chat_response:
                print("✅ Chat greeting successful")
                print(f"   Response: {chat_response['message'][:100]}...")
            else:
                print(f"❌ Invalid chat response format: {chat_response}")
        else:
            print(f"❌ Invalid response structure: {response}")

    async def test_chat_activity_query(self):
        """Test POST /api/chat asking about specific activity"""
        print("\n🔍 Testing Chat - Activity Info Query...")
        
        data = {
            "session_id": self.session_id,
            "message": "Tell me about Burj Khalifa"
        }
        
        response, error = await self.make_request("POST", "/chat", data)
        if error:
            print(f"❌ Chat activity query failed: {error}")
            return
            
        if response.get("status") == "ok" and "response" in response:
            chat_response = response["response"]
            if chat_response.get("type") == "activity_info":
                activity = chat_response.get("activity", {})
                if activity.get("id") == "burj-khalifa" and activity.get("image"):
                    print("✅ Chat activity info successful")
                    print(f"   Activity: {activity['name']}")
                    print(f"   Image enriched: {'✅' if activity.get('image') else '❌'}")
                else:
                    print(f"❌ Activity info missing or not enriched: {activity}")
            else:
                print(f"❌ Expected activity_info type, got: {chat_response.get('type')}")
        else:
            print(f"❌ Invalid response structure: {response}")

    async def test_chat_activity_listing(self):
        """Test POST /api/chat asking for activity list"""
        print("\n🔍 Testing Chat - Activity Listing...")
        
        data = {
            "session_id": self.session_id,
            "message": "What activities are available in Dubai?"
        }
        
        response, error = await self.make_request("POST", "/chat", data)
        if error:
            print(f"❌ Chat activity listing failed: {error}")
            return
            
        if response.get("status") == "ok" and "response" in response:
            chat_response = response["response"]
            if chat_response.get("type") == "activity_list":
                activities = chat_response.get("activities", [])
                if len(activities) > 0:
                    print(f"✅ Chat activity listing successful ({len(activities)} activities)")
                    # Check image enrichment
                    sample_activity = activities[0]
                    if sample_activity.get("image"):
                        print("✅ Activities have enriched images")
                    else:
                        print("❌ Activities missing enriched images")
                else:
                    print("❌ No activities in listing response")
            else:
                print(f"❌ Expected activity_list type, got: {chat_response.get('type')}")
        else:
            print(f"❌ Invalid response structure: {response}")

    async def test_chat_escalation(self):
        """Test POST /api/chat with unavailable activity (helicopter tour)"""
        print("\n🔍 Testing Chat - Escalation Flow...")
        
        data = {
            "session_id": self.session_id,
            "message": "I want to book a helicopter tour around Dubai"
        }
        
        response, error = await self.make_request("POST", "/chat", data)
        if error:
            print(f"❌ Chat escalation test failed: {error}")
            return
            
        if response.get("status") == "ok" and "response" in response:
            chat_response = response["response"]
            if chat_response.get("type") == "escalation":
                escalation_data = chat_response.get("escalation", {})
                email_sent = chat_response.get("email_sent")
                
                print("✅ Escalation flow triggered")
                print(f"   Reason: {escalation_data.get('reason', 'N/A')}")
                print(f"   Email sent: {'✅' if email_sent else '❌'}")
                
                if not email_sent:
                    print("⚠️  Email not sent - check email service configuration")
            else:
                print(f"❌ Expected escalation type, got: {chat_response.get('type')}")
        else:
            print(f"❌ Invalid response structure: {response}")

    async def test_chat_booking_flow(self):
        """Test POST /api/chat with complete booking"""
        print("\n🔍 Testing Chat - Booking Flow...")
        
        data = {
            "session_id": self.session_id,
            "message": "Book Burj Khalifa Standard for 2 people at 12:00, name is Sarah Johnson"
        }
        
        response, error = await self.make_request("POST", "/chat", data)
        if error:
            print(f"❌ Chat booking test failed: {error}")
            return
            
        if response.get("status") == "ok" and "response" in response:
            chat_response = response["response"]
            if chat_response.get("type") == "booking":
                booking_data = chat_response.get("booking", {})
                required_fields = ["activity_id", "activity_name", "customer_name", "total_price", "booking_id"]
                
                missing_fields = [field for field in required_fields if not booking_data.get(field)]
                if not missing_fields:
                    print("✅ Booking flow successful")
                    print(f"   Activity: {booking_data['activity_name']}")
                    print(f"   Customer: {booking_data['customer_name']}")
                    print(f"   Total: {booking_data['total_price']} {booking_data.get('currency', 'AED')}")
                    print(f"   Booking ID: {booking_data['booking_id']}")
                else:
                    print(f"❌ Booking missing required fields: {missing_fields}")
            else:
                print(f"❌ Expected booking type, got: {chat_response.get('type')}")
        else:
            print(f"❌ Invalid response structure: {response}")

    # ===============================
    # HISTORY & BOOKING TESTS
    # ===============================

    async def test_conversation_history(self):
        """Test GET /api/conversations/{session_id}"""
        print("\n🔍 Testing Conversation History...")
        
        response, error = await self.make_request("GET", f"/conversations/{self.session_id}")
        if error:
            print(f"❌ Conversation history failed: {error}")
            return
            
        messages = response.get("messages", [])
        if len(messages) > 0:
            print(f"✅ Conversation history retrieved ({len(messages)} messages)")
            
            # Check message structure
            sample_message = messages[0]
            required_fields = ["id", "session_id", "role", "content", "timestamp"]
            missing_fields = [field for field in required_fields if field not in sample_message]
            
            if not missing_fields:
                print("✅ Message structure is correct")
            else:
                print(f"❌ Message missing fields: {missing_fields}")
        else:
            print("⚠️  No conversation history found (expected after chat tests)")

    async def test_get_bookings(self):
        """Test GET /api/bookings/{session_id}"""
        print("\n🔍 Testing Get Bookings...")
        
        response, error = await self.make_request("GET", f"/bookings/{self.session_id}")
        if error:
            print(f"❌ Get bookings failed: {error}")
            return
            
        bookings = response.get("bookings", [])
        if len(bookings) > 0:
            print(f"✅ Bookings retrieved ({len(bookings)} bookings)")
            
            # Check booking structure
            sample_booking = bookings[0]
            required_fields = ["id", "session_id", "activity_id", "activity_name", "customer_name", "status"]
            missing_fields = [field for field in required_fields if field not in sample_booking]
            
            if not missing_fields:
                print("✅ Booking structure is correct")
            else:
                print(f"❌ Booking missing fields: {missing_fields}")
        else:
            print("⚠️  No bookings found (expected after booking test)")

    async def test_supervisor_reply(self):
        """Test POST /api/supervisor/reply"""
        print("\n🔍 Testing Supervisor Reply...")
        
        data = {
            "session_id": self.session_id,
            "message": "Thank you for your inquiry about helicopter tours. We can arrange a special helicopter experience for you. Please call +971-4-XXX-XXXX for booking."
        }
        
        response, error = await self.make_request("POST", "/supervisor/reply", data)
        if error:
            print(f"❌ Supervisor reply failed: {error}")
            return
            
        if response.get("status") == "ok":
            print("✅ Supervisor reply successful")
            print(f"   Message: {response.get('message', 'N/A')}")
        else:
            print(f"❌ Invalid supervisor reply response: {response}")

    def print_summary(self):
        """Print test results summary."""
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        print(f"Total Tests: {self.results['total_tests']}")
        print(f"Passed: {self.results['passed']} ✅")
        print(f"Failed: {self.results['failed']} ❌")
        
        if self.results['failed'] > 0:
            print(f"\nFAILED TESTS ({self.results['failed']}):")
            for i, error in enumerate(self.results['errors'], 1):
                print(f"{i}. {error}")
        
        success_rate = (self.results['passed'] / self.results['total_tests'] * 100) if self.results['total_tests'] > 0 else 0
        print(f"\nSuccess Rate: {success_rate:.1f}%")
        
        if success_rate >= 90:
            print("🎉 EXCELLENT - Backend APIs are working great!")
        elif success_rate >= 75:
            print("👍 GOOD - Most APIs working, minor issues to fix")
        elif success_rate >= 50:
            print("⚠️  MODERATE - Several issues need attention")
        else:
            print("🚨 CRITICAL - Major issues with backend APIs")

async def main():
    """Run all backend tests."""
    tester = DubaiTravelAssistantTests()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())