#!/usr/bin/env python3
"""
ACTIFY Daily Activity Reveal Automation Script
Simulates daily reveals for both global and group activities
"""

import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
import random

API_BASE = "http://localhost:8001/api"
ADMIN_USER_ID = "967c04e7-47ae-487d-8226-183d390c7808"
TEST_GROUP_ID = "e4818c1d-9547-4bb9-8d65-62ab55ef9515"

async def reveal_global_activity():
    """Simulate global activity reveal (happens automatically)"""
    print(f"🌍 GLOBAL ACTIVITY REVEAL - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    async with aiohttp.ClientSession() as session:
        # Get current global activity (auto-generates if needed)
        async with session.get(f"{API_BASE}/daily-global-activity/current") as response:
            if response.status == 200:
                data = await response.json()
                print(f"   📋 Today's Global Challenge: {data['activity_title']}")
                print(f"   📝 Description: {data['activity_description']}")
                print(f"   👥 Participants: {data['participant_count']}")
                print(f"   ⏰ Selected at: {data['selected_at']}")
                return True
            else:
                print(f"   ❌ Error getting global activity: {response.status}")
                return False

async def reveal_group_activity(group_id, day_number):
    """Simulate group activity reveal (admin-triggered)"""
    print(f"👥 GROUP ACTIVITY REVEAL - Day {day_number}")
    
    async with aiohttp.ClientSession() as session:
        # Prepare form data for reveal
        form_data = aiohttp.FormData()
        form_data.add_field('admin_id', ADMIN_USER_ID)
        form_data.add_field('day_number', str(day_number))
        
        async with session.post(f"{API_BASE}/groups/{group_id}/reveal-daily-activity", data=form_data) as response:
            if response.status == 200:
                data = await response.json()
                if data.get('success'):
                    activity = data['revealed_activity']
                    print(f"   🎯 Revealed: {activity['activity_title']}")
                    print(f"   📝 Description: {activity['activity_description']}")
                    print(f"   📅 Day {activity['day_number']} of 7")
                    print(f"   ⏰ Revealed at: {activity['revealed_at']}")
                    return True
                else:
                    print(f"   ❌ Reveal failed: {data.get('message', 'Unknown error')}")
                    return False
            else:
                error_data = await response.json()
                print(f"   ❌ Error revealing activity: {error_data.get('detail', 'Unknown error')}")
                return False

async def get_group_status(group_id):
    """Get current group status and next day to reveal"""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_BASE}/groups/{group_id}/weekly-activities") as response:
            if response.status == 200:
                activities = await response.json()
                revealed_count = sum(1 for activity in activities if activity.get('is_revealed', False))
                total_activities = len(activities)
                next_day = revealed_count + 1
                
                print(f"📊 GROUP STATUS:")
                print(f"   📝 Activities Submitted: {total_activities}/7")
                print(f"   👁️  Activities Revealed: {revealed_count}")
                print(f"   ➡️  Next Day to Reveal: {next_day}")
                
                return next_day if next_day <= 7 and total_activities >= next_day else None
            return None

async def simulate_daily_reveals():
    """Simulate the daily reveal process for both global and group activities"""
    print("🚀 ACTIFY DAILY REVEAL SIMULATION")
    print("=" * 50)
    
    # 1. Reveal Global Activity
    global_success = await reveal_global_activity()
    print()
    
    # 2. Check Group Status
    next_day = await get_group_status(TEST_GROUP_ID)
    print()
    
    # 3. Reveal Group Activity (if applicable)
    if next_day:
        group_success = await reveal_group_activity(TEST_GROUP_ID, next_day)
    else:
        print("👥 GROUP ACTIVITY REVEAL - No activities to reveal")
        print("   ℹ️  Either all activities revealed or insufficient submissions")
        group_success = False
    
    print()
    print("📊 REVEAL SUMMARY:")
    print(f"   🌍 Global Activity: {'✅ Success' if global_success else '❌ Failed'}")
    print(f"   👥 Group Activity: {'✅ Success' if next_day and group_success else '❌ Not Available'}")
    
    return global_success, (group_success if next_day else False)

async def schedule_reveals_for_week():
    """Simulate reveals for an entire week"""
    print("📅 SIMULATING WEEK-LONG REVEAL SCHEDULE")
    print("=" * 50)
    
    for day in range(1, 8):  # 7 days
        print(f"\n🗓️  DAY {day} SIMULATION:")
        print("-" * 30)
        
        # Simulate global activity (happens daily)
        await reveal_global_activity()
        print()
        
        # Simulate group activity reveal (one per day)
        await reveal_group_activity(TEST_GROUP_ID, day)
        
        # Add delay to simulate real timing
        await asyncio.sleep(1)
    
    print("\n🎉 WEEK SIMULATION COMPLETE!")

if __name__ == "__main__":
    print("ACTIFY REVEAL AUTOMATION SCRIPT")
    print("Choose simulation mode:")
    print("1. Single Daily Reveal (Today)")
    print("2. Full Week Simulation")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        asyncio.run(simulate_daily_reveals())
    elif choice == "2":
        asyncio.run(schedule_reveals_for_week())
    else:
        print("Invalid choice. Running single daily reveal...")
        asyncio.run(simulate_daily_reveals())