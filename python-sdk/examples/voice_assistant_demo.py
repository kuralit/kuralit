"""Voice Assistant Demo - Complete Voice Assistant with Multiple Tools

This example demonstrates a comprehensive voice assistant implementation with
multiple integrated tools for calendar, weather, reminders, and notes. This
shows how to combine multiple toolkits to create a powerful assistant.

Usage:
    python examples/voice_assistant_demo.py

Required Environment Variables (set in .env file or environment):
    - DEEPGRAM_API_KEY: API key for Deepgram STT service
    - GEMINI_API_KEY: API key for Google Gemini LLM
    - KURALIT_API_KEY: API key for client authentication (defaults to "demo-api-key")

Features:
    - Calendar management: Add, list, and delete events
    - Weather information: Get current weather and forecasts
    - Reminders: Create, list, and complete reminders
    - Notes: Create, list, and search notes
    - Calculator: Perform mathematical calculations

Example interactions:
    - "Add a meeting tomorrow at 2pm"
    - "What's the weather in San Francisco?"
    - "Remind me to call John at 5pm"
    - "Create a note about the project ideas"
    - "What reminders do I have?"
    - "What's 15 times 23?"

Note: This demo uses in-memory storage. Data is lost when the server restarts.
In production, you would connect to a database or external service.
"""

import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from uuid import uuid4

# Step 1: Import required modules
from kuralit.server.agent_session import AgentSession
from kuralit.server.config import ServerConfig
from kuralit.server.websocket_server import create_app
from kuralit.tools.toolkit import Toolkit


# Step 2: In-memory storage for demo data
# In production, these would be replaced with database connections
CALENDAR_EVENTS: Dict[str, Dict] = {}
REMINDERS: Dict[str, Dict] = {}
NOTES: Dict[str, Dict] = {}


# Step 3: Calendar Tools
# These functions manage calendar events

def add_event(title: str, date: str, time: str) -> str:
    """Add an event to the calendar.
    
    Args:
        title: Event title/description
        date: Event date (e.g., "2024-01-15" or "tomorrow")
        time: Event time (e.g., "14:00" or "2pm")
        
    Returns:
        Confirmation message with event ID
    """
    event_id = str(uuid4())
    
    # Parse date (simple implementation - in production use date parser)
    if date.lower() == "today":
        event_date = datetime.now().date()
    elif date.lower() == "tomorrow":
        event_date = (datetime.now() + timedelta(days=1)).date()
    else:
        try:
            event_date = datetime.strptime(date, "%Y-%m-%d").date()
        except:
            event_date = datetime.now().date()
    
    CALENDAR_EVENTS[event_id] = {
        "id": event_id,
        "title": title,
        "date": str(event_date),
        "time": time,
        "created_at": datetime.now().isoformat()
    }
    
    return f"Event added: '{title}' on {event_date} at {time} (ID: {event_id})"


def list_events(date: Optional[str] = None) -> str:
    """List calendar events.
    
    Args:
        date: Optional date filter (e.g., "2024-01-15" or "today")
        
    Returns:
        Formatted list of events
    """
    if not CALENDAR_EVENTS:
        return "No events in calendar."
    
    events = list(CALENDAR_EVENTS.values())
    
    # Filter by date if provided
    if date:
        if date.lower() == "today":
            today = datetime.now().date()
            events = [e for e in events if e["date"] == str(today)]
        elif date.lower() == "tomorrow":
            tomorrow = (datetime.now() + timedelta(days=1)).date()
            events = [e for e in events if e["date"] == str(tomorrow)]
        else:
            events = [e for e in events if e["date"] == date]
    
    if not events:
        return f"No events found for {date or 'any date'}."
    
    result = f"Found {len(events)} event(s):\n"
    for event in events:
        result += f"  - {event['title']} on {event['date']} at {event['time']} (ID: {event['id']})\n"
    
    return result.strip()


def delete_event(event_id: str) -> str:
    """Delete an event from the calendar.
    
    Args:
        event_id: The event ID to delete
        
    Returns:
        Confirmation message
    """
    if event_id in CALENDAR_EVENTS:
        title = CALENDAR_EVENTS[event_id]["title"]
        del CALENDAR_EVENTS[event_id]
        return f"Event '{title}' (ID: {event_id}) deleted."
    else:
        return f"Event with ID {event_id} not found."


# Step 4: Weather Tools
# These functions provide weather information (mock implementation)

def get_weather(location: str) -> str:
    """Get current weather for a location.
    
    Args:
        location: City name or location
        
    Returns:
        Weather information
    """
    # Mock weather data - in production, call OpenWeatherMap or similar API
    mock_weather = {
        "san francisco": "Sunny, 18°C, Light breeze",
        "new york": "Partly cloudy, 15°C, Moderate wind",
        "london": "Cloudy, 12°C, Light rain",
        "tokyo": "Clear, 22°C, Calm",
        "paris": "Sunny, 16°C, Light breeze",
    }
    
    location_lower = location.lower()
    weather = mock_weather.get(location_lower, "Partly cloudy, 20°C, Light breeze")
    return f"Weather in {location}: {weather}"


def get_forecast(location: str, days: int = 3) -> str:
    """Get weather forecast for a location.
    
    Args:
        location: City name or location
        days: Number of days to forecast (default: 3)
        
    Returns:
        Weather forecast
    """
    # Mock forecast - in production, call weather API
    return f"3-day forecast for {location}:\n" \
           f"  Day 1: Sunny, 20°C\n" \
           f"  Day 2: Partly cloudy, 18°C\n" \
           f"  Day 3: Light rain, 16°C"


# Step 5: Reminder Tools
# These functions manage reminders

def create_reminder(text: str, due_date: Optional[str] = None) -> str:
    """Create a reminder.
    
    Args:
        text: Reminder text/description
        due_date: Optional due date/time
        
    Returns:
        Confirmation message with reminder ID
    """
    reminder_id = str(uuid4())
    REMINDERS[reminder_id] = {
        "id": reminder_id,
        "text": text,
        "due_date": due_date,
        "completed": False,
        "created_at": datetime.now().isoformat()
    }
    
    return f"Reminder created: '{text}' (ID: {reminder_id})" + \
           (f" due {due_date}" if due_date else "")


def list_reminders(completed: bool = False) -> str:
    """List reminders.
    
    Args:
        completed: If True, show only completed reminders
        
    Returns:
        Formatted list of reminders
    """
    reminders = [r for r in REMINDERS.values() if r["completed"] == completed]
    
    if not reminders:
        status = "completed" if completed else "pending"
        return f"No {status} reminders."
    
    result = f"Found {len(reminders)} {'completed' if completed else 'pending'} reminder(s):\n"
    for reminder in reminders:
        status = "✓" if reminder["completed"] else "○"
        due = f" (due: {reminder['due_date']})" if reminder["due_date"] else ""
        result += f"  {status} {reminder['text']}{due} (ID: {reminder['id']})\n"
    
    return result.strip()


def complete_reminder(reminder_id: str) -> str:
    """Mark a reminder as completed.
    
    Args:
        reminder_id: The reminder ID to complete
        
    Returns:
        Confirmation message
    """
    if reminder_id in REMINDERS:
        REMINDERS[reminder_id]["completed"] = True
        text = REMINDERS[reminder_id]["text"]
        return f"Reminder '{text}' (ID: {reminder_id}) marked as completed."
    else:
        return f"Reminder with ID {reminder_id} not found."


# Step 6: Note Tools
# These functions manage notes

def create_note(title: str, content: str) -> str:
    """Create a note.
    
    Args:
        title: Note title
        content: Note content
        
    Returns:
        Confirmation message with note ID
    """
    note_id = str(uuid4())
    NOTES[note_id] = {
        "id": note_id,
        "title": title,
        "content": content,
        "created_at": datetime.now().isoformat()
    }
    
    return f"Note created: '{title}' (ID: {note_id})"


def list_notes() -> str:
    """List all notes.
    
    Returns:
        Formatted list of notes
    """
    if not NOTES:
        return "No notes found."
    
    result = f"Found {len(NOTES)} note(s):\n"
    for note in NOTES.values():
        result += f"  - {note['title']} (ID: {note['id']})\n"
    
    return result.strip()


def search_notes(query: str) -> str:
    """Search notes by title or content.
    
    Args:
        query: Search query
        
    Returns:
        Matching notes
    """
    query_lower = query.lower()
    matches = []
    
    for note in NOTES.values():
        if query_lower in note["title"].lower() or query_lower in note["content"].lower():
            matches.append(note)
    
    if not matches:
        return f"No notes found matching '{query}'."
    
    result = f"Found {len(matches)} matching note(s):\n"
    for note in matches:
        result += f"  - {note['title']}: {note['content'][:50]}... (ID: {note['id']})\n"
    
    return result.strip()


# Step 7: Calculator Tool (reused from simple_tools_demo)
def calculate(expression: str) -> str:
    """Calculate a mathematical expression."""
    try:
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"Error calculating expression: {str(e)}"


# Step 8: API key validator
def validate_api_key(api_key: str) -> bool:
    """Validate API key from client connection."""
    expected_key = os.getenv("KURALIT_API_KEY", "demo-api-key")
    return api_key == expected_key


if __name__ == "__main__":
    import uvicorn
    
    # Step 9: Create domain-specific toolkits
    # Group related tools together for better organization
    calendar_tools = Toolkit(
        name="calendar",
        tools=[add_event, list_events, delete_event],
        instructions="Calendar tools for managing events. Use add_event to create new events, "
                    "list_events to view events, and delete_event to remove events."
    )
    
    weather_tools = Toolkit(
        name="weather",
        tools=[get_weather, get_forecast],
        instructions="Weather tools for getting current weather and forecasts. "
                    "Use get_weather for current conditions and get_forecast for multi-day forecasts."
    )
    
    reminder_tools = Toolkit(
        name="reminders",
        tools=[create_reminder, list_reminders, complete_reminder],
        instructions="Reminder tools for managing reminders. Use create_reminder to add reminders, "
                    "list_reminders to view them, and complete_reminder to mark them as done."
    )
    
    note_tools = Toolkit(
        name="notes",
        tools=[create_note, list_notes, search_notes],
        instructions="Note tools for managing notes. Use create_note to add notes, "
                    "list_notes to view all notes, and search_notes to find specific notes."
    )
    
    calculator_tools = Toolkit(
        name="calculator",
        tools=[calculate],
        instructions="Calculator tool for performing mathematical calculations."
    )
    
    # Step 10: Create AgentSession with all toolkits
    agent_session = AgentSession(
        stt="deepgram/nova-2:en-US",
        llm="gemini/gemini-2.0-flash-001",
        vad="silero/v3",
        turn_detection="multilingual/v1",
        
        # Pass all toolkits to the agent
        tools=[calendar_tools, weather_tools, reminder_tools, note_tools, calculator_tools],
        
        # Comprehensive instructions for the voice assistant
        instructions="""You are a comprehensive voice assistant with access to multiple tools.
        
You can help users with:
- Calendar: Add, list, and delete events
- Weather: Get current weather and forecasts for any location
- Reminders: Create, list, and complete reminders
- Notes: Create, list, and search notes
- Calculations: Perform mathematical calculations

When users make requests:
1. Identify which tool(s) are needed
2. Use the appropriate tool(s) to fulfill the request
3. Provide clear, helpful responses
4. For destructive actions (like deleting events), confirm with the user first

Always be helpful, concise, and provide context in your responses.""",
        
        name="Voice Assistant",
    )
    
    # Step 11: Create FastAPI application
    app = create_app(
        api_key_validator=validate_api_key,
        agent_session=agent_session,
    )
    
    # Step 12: Get server configuration
    config = agent_session._config.server if agent_session._config else ServerConfig()
    
    # Step 13: Start the server
    print("🚀 Starting Voice Assistant server...")
    print(f"   Host: {config.host}")
    print(f"   Port: {config.port}")
    print(f"   Connect at: ws://{config.host}:{config.port}/ws")
    print("\n   Available features:")
    print("   📅 Calendar: Add, list, delete events")
    print("   🌤️  Weather: Current weather and forecasts")
    print("   ⏰ Reminders: Create, list, complete reminders")
    print("   📝 Notes: Create, list, search notes")
    print("   🔢 Calculator: Mathematical calculations")
    print("\n   Example requests:")
    print("   - 'Add a meeting tomorrow at 2pm'")
    print("   - 'What's the weather in San Francisco?'")
    print("   - 'Remind me to call John at 5pm'")
    print("   - 'Create a note about project ideas'")
    print("   - 'What's 15 times 23?'")
    print("\n   Press Ctrl+C to stop the server\n")
    
    uvicorn.run(
        app,
        host=config.host,
        port=config.port,
        log_level=config.log_level.lower(),
    )

