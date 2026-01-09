"""
Conversation Manager - ChatGPT-style multi-chat system
Manages multiple conversations with LLM-generated titles
"""

import logging
import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

class ConversationManager:
    """
    Manages multiple conversations per user with LLM-generated titles
    """
    
    def __init__(self, db_path: str = "users_db.json"):
        self.db_path = db_path
        
        # Initialize Groq for title generation
        self.groq_key = os.getenv('GROQ_API_KEY')
        if self.groq_key and GROQ_AVAILABLE:
            self.groq = Groq(api_key=self.groq_key)
            self.llm_available = True
        else:
            self.groq = None
            self.llm_available = False
    
    def create_conversation(self, user_id: str, initial_message: str = None) -> Dict[str, Any]:
        """
        Create a new conversation for user
        Returns conversation object with ID
        """
        conversation_id = str(uuid.uuid4())
        
        # Generate title from first message using LLM
        if initial_message and self.llm_available:
            title = self._generate_title(initial_message)
        else:
            title = f"New Chat {datetime.now().strftime('%b %d, %I:%M %p')}"
        
        conversation = {
            'conversation_id': conversation_id,
            'title': title,
            'messages': [],
            'created_at': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat(),
            'user_id': user_id
        }
        
        # Save to database
        self._save_conversation(user_id, conversation)
        
        logger.info(f"✅ Created conversation: {conversation_id} - '{title}'")
        
        return conversation
    
    def _generate_title(self, first_message: str) -> str:
        """
        Use LLM to generate a short, descriptive title from the first message
        """
        if not self.llm_available:
            return f"Chat {datetime.now().strftime('%b %d')}"
        
        try:
            # Limit message length for title generation
            message_preview = first_message[:200]
            
            response = self.groq.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": "Generate a very short (2-5 words) descriptive title for this conversation. Be specific and concise. Examples: 'Apple Investment Analysis', 'Portfolio Review', 'Tesla vs Microsoft', 'Withdrawal Planning'"
                    },
                    {
                        "role": "user",
                        "content": f"Generate a title for a conversation that starts with: \"{message_preview}\""
                    }
                ],
                temperature=0.5,
                max_tokens=20
            )
            
            title = response.choices[0].message.content.strip()
            
            # Clean up title (remove quotes if LLM added them)
            title = title.strip('"').strip("'")
            
            # Limit length
            if len(title) > 40:
                title = title[:37] + "..."
            
            logger.info(f"✅ Generated title: '{title}'")
            return title
            
        except Exception as e:
            logger.error(f"Error generating title: {e}")
            return f"Chat {datetime.now().strftime('%b %d')}"
    
    def get_user_conversations(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all conversations for a user, sorted by most recent
        """
        try:
            if not os.path.exists(self.db_path):
                return []
            
            with open(self.db_path, 'r') as f:
                db = json.load(f)
            
            # Find user
            for email, user_data in db.items():
                if isinstance(user_data, dict) and user_data.get('user_id') == user_id:
                    conversations = user_data.get('conversations', [])
                    
                    # Sort by last_updated (most recent first)
                    conversations.sort(key=lambda c: c.get('last_updated', ''), reverse=True)
                    
                    logger.info(f"✅ Found {len(conversations)} conversations for {user_id}")
                    return conversations
            
            return []
            
        except Exception as e:
            logger.error(f"Error loading conversations: {e}")
            return []
    
    def get_conversation(self, user_id: str, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific conversation by ID"""
        conversations = self.get_user_conversations(user_id)
        
        for conv in conversations:
            if conv.get('conversation_id') == conversation_id:
                return conv
        
        return None
    
    def add_message(self, 
                   user_id: str,
                   conversation_id: str,
                   role: str,
                   content: str) -> bool:
        """
        Add a message to a conversation
        """
        try:
            conversations = self.get_user_conversations(user_id)
            
            # Find conversation
            for conv in conversations:
                if conv.get('conversation_id') == conversation_id:
                    conv['messages'].append({
                        'role': role,
                        'content': content,
                        'timestamp': datetime.now().isoformat()
                    })
                    conv['last_updated'] = datetime.now().isoformat()
                    
                    # Save back
                    self._save_all_conversations(user_id, conversations)
                    return True
            
            logger.warning(f"Conversation {conversation_id} not found")
            return False
            
        except Exception as e:
            logger.error(f"Error adding message: {e}")
            return False
    
    def rename_conversation(self, 
                           user_id: str,
                           conversation_id: str,
                           new_title: str) -> bool:
        """Rename a conversation"""
        try:
            conversations = self.get_user_conversations(user_id)
            
            for conv in conversations:
                if conv.get('conversation_id') == conversation_id:
                    conv['title'] = new_title
                    conv['last_updated'] = datetime.now().isoformat()
                    
                    self._save_all_conversations(user_id, conversations)
                    logger.info(f"✅ Renamed conversation to: '{new_title}'")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error renaming conversation: {e}")
            return False
    
    def delete_conversation(self, user_id: str, conversation_id: str) -> bool:
        """Delete a conversation"""
        try:
            conversations = self.get_user_conversations(user_id)
            
            # Filter out the conversation to delete
            updated_conversations = [c for c in conversations if c.get('conversation_id') != conversation_id]
            
            if len(updated_conversations) < len(conversations):
                self._save_all_conversations(user_id, updated_conversations)
                logger.info(f"✅ Deleted conversation: {conversation_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting conversation: {e}")
            return False
    
    def _save_conversation(self, user_id: str, conversation: Dict[str, Any]):
        """Save a new conversation to database"""
        conversations = self.get_user_conversations(user_id)
        conversations.append(conversation)
        self._save_all_conversations(user_id, conversations)
    
    def _save_all_conversations(self, user_id: str, conversations: List[Dict[str, Any]]):
        """Save all conversations for a user"""
        try:
            if os.path.exists(self.db_path):
                with open(self.db_path, 'r') as f:
                    db = json.load(f)
            else:
                db = {}
            
            # Find user and update conversations
            user_found = False
            for email, user_data in db.items():
                if isinstance(user_data, dict) and user_data.get('user_id') == user_id:
                    user_data['conversations'] = conversations
                    user_found = True
                    break
            
            # If user not found, create a new entry using user_id as the key
            if not user_found:
                db[user_id] = {
                    'user_id': user_id,
                    'conversations': conversations,
                    'created_at': datetime.now().isoformat()
                }
                logger.info(f"✅ Created new user entry for {user_id}")
            
            # Save
            with open(self.db_path, 'w') as f:
                json.dump(db, f, indent=2)
            
            logger.info(f"✅ Saved {len(conversations)} conversations for {user_id}")
            
        except Exception as e:
            logger.error(f"Error saving conversations: {e}")


# Global instance
_conversation_manager = None

def get_conversation_manager() -> ConversationManager:
    """Get or create conversation manager singleton"""
    global _conversation_manager
    if _conversation_manager is None:
        _conversation_manager = ConversationManager()
    return _conversation_manager


if __name__ == "__main__":
    # Test conversation manager
    cm = ConversationManager()
    
    print("\n🧪 Testing Conversation Manager\n")
    
    # Create conversation
    conv = cm.create_conversation("test_user", "Should I invest in Apple?")
    print(f"Created: {conv['title']}")
    print(f"ID: {conv['conversation_id']}")
    
    # Add message
    cm.add_message("test_user", conv['conversation_id'], "user", "What about Tesla?")
    cm.add_message("test_user", conv['conversation_id'], "assistant", "Tesla is interesting...")
    
    # Get conversations
    all_convs = cm.get_user_conversations("test_user")
    print(f"\nTotal conversations: {len(all_convs)}")
    for c in all_convs:
        print(f"  - {c['title']} ({len(c['messages'])} messages)")
    
    # Rename
    cm.rename_conversation("test_user", conv['conversation_id'], "Apple & Tesla Research")
    print(f"\nRenamed to: 'Apple & Tesla Research'")


