#!/bin/bash
# ACTIFY Daily Activity Reveal Automation Script

API_BASE="http://localhost:8001/api"
ADMIN_USER_ID="967c04e7-47ae-487d-8226-183d390c7808"
TEST_GROUP_ID="e4818c1d-9547-4bb9-8d65-62ab55ef9515"

echo "🚀 ACTIFY DAILY REVEAL SIMULATION"
echo "=================================="
echo "Current time: $(date)"
echo ""

# Function to reveal global activity
reveal_global_activity() {
    echo "🌍 GLOBAL ACTIVITY REVEAL"
    echo "-------------------------"
    
    response=$(curl -s -X GET "$API_BASE/daily-global-activity/current")
    title=$(echo "$response" | jq -r '.activity_title')
    description=$(echo "$response" | jq -r '.activity_description')
    participants=$(echo "$response" | jq -r '.participant_count')
    selected_at=$(echo "$response" | jq -r '.selected_at')
    
    echo "   📋 Today's Global Challenge: $title"
    echo "   📝 Description: $description"
    echo "   👥 Participants: $participants"
    echo "   ⏰ Selected at: $selected_at"
    echo ""
}

# Function to get next day to reveal for group
get_next_reveal_day() {
    local group_id=$1
    
    echo "📊 GROUP STATUS:"
    
    # Get weekly activities and count revealed ones
    response=$(curl -s -X GET "$API_BASE/groups/$group_id/weekly-activities")
    total=$(echo "$response" | jq 'length')
    revealed=$(echo "$response" | jq '[.[] | select(.is_revealed == true)] | length')
    next_day=$((revealed + 1))
    
    echo "   📝 Activities Submitted: $total/7"
    echo "   👁️  Activities Revealed: $revealed"
    echo "   ➡️  Next Day to Reveal: $next_day"
    echo ""
    
    if [ $next_day -le 7 ] && [ $total -ge $next_day ]; then
        return $next_day
    else
        return 0
    fi
}

# Function to reveal group activity
reveal_group_activity() {
    local group_id=$1
    local day_number=$2
    
    echo "👥 GROUP ACTIVITY REVEAL - Day $day_number"
    echo "----------------------------------------"
    
    if [ $day_number -eq 0 ]; then
        echo "   ℹ️  No activities available to reveal"
        echo "   💡 Either all activities revealed or insufficient submissions"
        return 1
    fi
    
    response=$(curl -s -X POST "$API_BASE/groups/$group_id/reveal-daily-activity" \
        -F "admin_id=$ADMIN_USER_ID" \
        -F "day_number=$day_number")
    
    success=$(echo "$response" | jq -r '.success')
    
    if [ "$success" = "true" ]; then
        title=$(echo "$response" | jq -r '.revealed_activity.activity_title')
        description=$(echo "$response" | jq -r '.revealed_activity.activity_description')
        revealed_at=$(echo "$response" | jq -r '.revealed_activity.revealed_at')
        
        echo "   🎯 Revealed: $title"
        echo "   📝 Description: $description"
        echo "   📅 Day $day_number of 7"
        echo "   ⏰ Revealed at: $revealed_at"
        echo "   ✅ SUCCESS"
        return 0
    else
        error=$(echo "$response" | jq -r '.detail // "Unknown error"')
        echo "   ❌ Error: $error"
        return 1
    fi
}

# Main simulation
main() {
    # 1. Reveal Global Activity
    reveal_global_activity
    
    # 2. Get group status and next day to reveal
    get_next_reveal_day $TEST_GROUP_ID
    next_day=$?
    
    # 3. Reveal Group Activity
    reveal_group_activity $TEST_GROUP_ID $next_day
    group_success=$?
    
    echo ""
    echo "📊 REVEAL SUMMARY:"
    echo "=================="
    echo "   🌍 Global Activity: ✅ Available"
    if [ $group_success -eq 0 ]; then
        echo "   👥 Group Activity: ✅ Successfully Revealed"
    else
        echo "   👥 Group Activity: ❌ Not Available/Failed"
    fi
    echo ""
    echo "🎉 Daily reveal simulation complete!"
}

# Run the simulation
main