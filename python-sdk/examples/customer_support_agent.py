"""Customer Support Agent - Customer Support Use Case

This example demonstrates a customer support agent with structured responses,
FAQ tools, ticket management, and account management capabilities.

Usage:
    python examples/customer_support_agent.py

Required Environment Variables (set in .env file or environment):
    - DEEPGRAM_API_KEY: API key for Deepgram STT service
    - GEMINI_API_KEY: API key for Google Gemini LLM
    - KURALIT_API_KEY: API key for client authentication (defaults to "demo-api-key")

Features:
    - FAQ Search: Search knowledge base for common questions
    - Ticket Management: Create, view, update, and list support tickets
    - Account Management: Get account and order information
    - Actions: Process refunds (with confirmation), escalate tickets

Example interactions:
    - "How do I reset my password?"
    - "I want to return my order"
    - "What's the status of ticket 12345?"
    - "I need a refund for order ABC123"

Note: This demo uses in-memory storage. Data is lost when the server restarts.
In production, you would connect to a ticketing system, knowledge base, and database.
"""

import os
from datetime import datetime
from typing import Dict, List, Optional
from uuid import uuid4

# Step 1: Import required modules
from kuralit.server.agent_session import AgentSession
from kuralit.server.config import ServerConfig
from kuralit.server.websocket_server import create_app
from kuralit.tools.toolkit import Toolkit


# Step 2: In-memory storage for demo data
# In production, these would be replaced with database connections
FAQ_DATABASE: List[Dict[str, str]] = [
    {
        "question": "How do I reset my password?",
        "answer": "To reset your password, go to the login page and click 'Forgot Password'. "
                 "Enter your email address and you'll receive a password reset link. "
                 "Click the link and follow the instructions to create a new password."
    },
    {
        "question": "How do I return an item?",
        "answer": "To return an item, go to your order history, select the order, and click 'Return Item'. "
                 "You can return items within 30 days of purchase. "
                 "A return label will be provided, and you'll receive a refund once we process the return."
    },
    {
        "question": "What is your refund policy?",
        "answer": "We offer full refunds for items returned within 30 days of purchase in original condition. "
                 "Refunds are processed within 5-7 business days after we receive the returned item."
    },
    {
        "question": "How do I track my order?",
        "answer": "You can track your order by going to your account and selecting 'Order History'. "
                 "Click on the order number to see tracking information and delivery status."
    },
    {
        "question": "How do I update my account information?",
        "answer": "To update your account information, go to your account settings. "
                 "You can update your email, phone number, shipping address, and payment methods."
    },
    {
        "question": "What payment methods do you accept?",
        "answer": "We accept all major credit cards (Visa, Mastercard, American Express), PayPal, "
                 "and Apple Pay. All payments are processed securely."
    },
]

TICKETS: Dict[str, Dict] = {}
ACCOUNTS: Dict[str, Dict] = {
    "CUST001": {
        "id": "CUST001",
        "name": "John Doe",
        "email": "john.doe@example.com",
        "orders": ["ORD001", "ORD002"]
    }
}
ORDERS: Dict[str, Dict] = {
    "ORD001": {
        "id": "ORD001",
        "customer_id": "CUST001",
        "total": 99.99,
        "status": "delivered",
        "date": "2024-01-15"
    },
    "ORD002": {
        "id": "ORD002",
        "customer_id": "CUST001",
        "total": 149.99,
        "status": "processing",
        "date": "2024-01-20"
    }
}


# Step 3: FAQ Tools
# These functions search the knowledge base

def search_faq(query: str) -> str:
    """Search the FAQ/knowledge base for answers.
    
    Args:
        query: Search query or question
        
    Returns:
        Relevant FAQ answers or "No matching FAQ found"
    """
    query_lower = query.lower()
    matches = []
    
    # Simple keyword matching - in production, use proper search engine
    for faq in FAQ_DATABASE:
        if query_lower in faq["question"].lower() or query_lower in faq["answer"].lower():
            matches.append(faq)
    
    if not matches:
        return f"No matching FAQ found for '{query}'. Would you like me to create a support ticket?"
    
    if len(matches) == 1:
        return f"Found answer:\nQ: {matches[0]['question']}\nA: {matches[0]['answer']}"
    
    result = f"Found {len(matches)} relevant answers:\n\n"
    for i, faq in enumerate(matches, 1):
        result += f"{i}. Q: {faq['question']}\n   A: {faq['answer']}\n\n"
    
    return result.strip()


# Step 4: Ticket Management Tools
# These functions manage support tickets

def create_ticket(subject: str, description: str, priority: str = "medium") -> str:
    """Create a support ticket.
    
    Args:
        subject: Ticket subject/title
        description: Detailed description of the issue
        priority: Ticket priority (low, medium, high, urgent)
        
    Returns:
        Confirmation message with ticket ID
    """
    ticket_id = f"TICKET-{str(uuid4())[:8].upper()}"
    TICKETS[ticket_id] = {
        "id": ticket_id,
        "subject": subject,
        "description": description,
        "priority": priority.lower(),
        "status": "open",
        "created_at": datetime.now().isoformat(),
        "notes": []
    }
    
    return f"Support ticket created:\n" \
           f"  Ticket ID: {ticket_id}\n" \
           f"  Subject: {subject}\n" \
           f"  Priority: {priority}\n" \
           f"  Status: Open\n\n" \
           f"Your ticket has been logged and will be reviewed by our support team."


def get_ticket_status(ticket_id: str) -> str:
    """Get the status of a support ticket.
    
    Args:
        ticket_id: The ticket ID to check
        
    Returns:
        Ticket status information
    """
    if ticket_id not in TICKETS:
        return f"Ticket {ticket_id} not found. Please check the ticket ID and try again."
    
    ticket = TICKETS[ticket_id]
    return f"Ticket {ticket_id}:\n" \
           f"  Subject: {ticket['subject']}\n" \
           f"  Status: {ticket['status'].title()}\n" \
           f"  Priority: {ticket['priority'].title()}\n" \
           f"  Created: {ticket['created_at']}"


def update_ticket(ticket_id: str, status: Optional[str] = None, notes: Optional[str] = None) -> str:
    """Update a support ticket.
    
    Args:
        ticket_id: The ticket ID to update
        status: New status (open, in_progress, resolved, closed)
        notes: Additional notes to add
        
    Returns:
        Confirmation message
    """
    if ticket_id not in TICKETS:
        return f"Ticket {ticket_id} not found."
    
    ticket = TICKETS[ticket_id]
    
    if status:
        ticket["status"] = status.lower()
    
    if notes:
        ticket["notes"].append({
            "note": notes,
            "timestamp": datetime.now().isoformat()
        })
    
    return f"Ticket {ticket_id} updated successfully. " \
           f"Status: {ticket['status'].title()}"


def list_tickets(customer_id: Optional[str] = None) -> str:
    """List support tickets.
    
    Args:
        customer_id: Optional customer ID to filter tickets
        
    Returns:
        List of tickets
    """
    if not TICKETS:
        return "No tickets found."
    
    tickets = list(TICKETS.values())
    
    # In production, filter by customer_id from database
    if customer_id:
        # This is a simplified filter - in production, tickets would have customer_id
        pass
    
    result = f"Found {len(tickets)} ticket(s):\n\n"
    for ticket in tickets:
        result += f"  {ticket['id']}: {ticket['subject']}\n" \
                 f"    Status: {ticket['status'].title()}, " \
                 f"Priority: {ticket['priority'].title()}\n"
    
    return result.strip()


# Step 5: Account Management Tools
# These functions provide account and order information

def get_account_info(customer_id: str) -> str:
    """Get customer account information.
    
    Args:
        customer_id: Customer ID
        
    Returns:
        Account information
    """
    if customer_id not in ACCOUNTS:
        return f"Account {customer_id} not found."
    
    account = ACCOUNTS[customer_id]
    return f"Account Information:\n" \
           f"  Customer ID: {account['id']}\n" \
           f"  Name: {account['name']}\n" \
           f"  Email: {account['email']}\n" \
           f"  Orders: {len(account['orders'])}"


def get_order_history(customer_id: str) -> str:
    """Get order history for a customer.
    
    Args:
        customer_id: Customer ID
        
    Returns:
        Order history
    """
    if customer_id not in ACCOUNTS:
        return f"Customer {customer_id} not found."
    
    account = ACCOUNTS[customer_id]
    order_ids = account.get("orders", [])
    
    if not order_ids:
        return f"No orders found for customer {customer_id}."
    
    result = f"Order History for {account['name']}:\n\n"
    for order_id in order_ids:
        if order_id in ORDERS:
            order = ORDERS[order_id]
            result += f"  {order_id}:\n" \
                     f"    Date: {order['date']}\n" \
                     f"    Total: ${order['total']:.2f}\n" \
                     f"    Status: {order['status'].title()}\n\n"
    
    return result.strip()


# Step 6: Action Tools
# These functions perform actions that may require confirmation

def process_refund(order_id: str, amount: float) -> str:
    """Process a refund for an order.
    
    WARNING: This function requires confirmation before execution.
    In production, this would integrate with payment processors.
    
    Args:
        order_id: Order ID to refund
        amount: Refund amount
        
    Returns:
        Refund confirmation or error message
    """
    if order_id not in ORDERS:
        return f"Order {order_id} not found."
    
    order = ORDERS[order_id]
    
    if amount > order["total"]:
        return f"Refund amount (${amount:.2f}) exceeds order total (${order['total']:.2f})."
    
    # In production, this would call payment processor API
    # For demo, we just return a confirmation message
    return f"Refund processed successfully:\n" \
           f"  Order: {order_id}\n" \
           f"  Amount: ${amount:.2f}\n" \
           f"  Refund will appear in 5-7 business days."


def escalate_ticket(ticket_id: str, reason: str) -> str:
    """Escalate a support ticket to higher priority.
    
    Args:
        ticket_id: Ticket ID to escalate
        reason: Reason for escalation
        
    Returns:
        Confirmation message
    """
    if ticket_id not in TICKETS:
        return f"Ticket {ticket_id} not found."
    
    ticket = TICKETS[ticket_id]
    ticket["priority"] = "urgent"
    ticket["notes"].append({
        "note": f"Escalated: {reason}",
        "timestamp": datetime.now().isoformat()
    })
    
    return f"Ticket {ticket_id} has been escalated to urgent priority. " \
           f"Our senior support team will review it immediately."


# Step 7: API key validator
def validate_api_key(api_key: str) -> bool:
    """Validate API key from client connection."""
    expected_key = os.getenv("KURALIT_API_KEY", "demo-api-key")
    return api_key == expected_key


if __name__ == "__main__":
    import uvicorn
    
    # Step 8: Create support toolkit with all tools
    support_tools = Toolkit(
        name="customer_support",
        tools=[
            search_faq,
            create_ticket,
            get_ticket_status,
            update_ticket,
            list_tickets,
            get_account_info,
            get_order_history,
            process_refund,
            escalate_ticket,
        ],
        instructions="Customer support tools for FAQ search, ticket management, "
                    "account information, and order management. Use search_faq first "
                    "before creating tickets. Process refunds only with user confirmation."
    )
    
    # Step 9: Create AgentSession with support persona
    agent_session = AgentSession(
        stt="deepgram/nova-2:en-US",
        llm="gemini/gemini-2.0-flash-001",
        vad="silero/v3",
        turn_detection="multilingual/v1",
        
        # Pass support toolkit
        tools=[support_tools],
        
        # Customer support agent instructions
        instructions="""You are a professional customer support agent.

Your responsibilities:
1. Be empathetic, patient, and solution-oriented
2. Always acknowledge the customer's concern first
3. Search the FAQ/knowledge base before creating tickets
4. Provide clear, step-by-step solutions
5. Use structured responses with clear formatting
6. Confirm before processing refunds or other sensitive actions
7. Escalate complex issues that you cannot resolve

Response format:
- Acknowledge the customer's issue
- Search FAQ if applicable
- Provide solution or create ticket
- Offer additional help

Be professional, friendly, and helpful. Always aim to resolve issues quickly and effectively.""",
        
        name="Customer Support Agent",
    )
    
    # Step 10: Create FastAPI application
    app = create_app(
        api_key_validator=validate_api_key,
        agent_session=agent_session,
    )
    
    # Step 11: Get server configuration
    config = agent_session._config.server if agent_session._config else ServerConfig()
    
    # Step 12: Start the server
    print("🚀 Starting Customer Support Agent server...")
    print(f"   Host: {config.host}")
    print(f"   Port: {config.port}")
    print(f"   Connect at: ws://{config.host}:{config.port}/ws")
    print("\n   Available features:")
    print("   📚 FAQ Search: Search knowledge base")
    print("   🎫 Ticket Management: Create, view, update tickets")
    print("   👤 Account Management: View account and order information")
    print("   💰 Actions: Process refunds, escalate tickets")
    print("\n   Example requests:")
    print("   - 'How do I reset my password?'")
    print("   - 'I want to return my order'")
    print("   - 'What's the status of ticket TICKET-12345678?'")
    print("   - 'I need a refund for order ORD001'")
    print("\n   Press Ctrl+C to stop the server\n")
    
    uvicorn.run(
        app,
        host=config.host,
        port=config.port,
        log_level=config.log_level.lower(),
    )

