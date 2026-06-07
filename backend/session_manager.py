# backend/session_manager.py
from typing import Dict, List, Any

class SessionManager:
    """
    Manages session context in-memory.
    Maintains history of last 5 queries, extracted entities, and filters.
    Compatible with future Redis implementations.
    """
    def __init__(self):
        # Format: { session_id: { "queries": List[str], "entities": List[Dict], "filters": Dict[str, Any] } }
        self._sessions: Dict[str, Dict[str, Any]] = {}

    def get_context(self, session_id: str) -> Dict[str, Any]:
        """Retrieves context dictionary for a session_id, creating one if not exists."""
        if not session_id:
            # Fallback for anonymous sessions
            session_id = "default_session"
            
        if session_id not in self._sessions:
            self._sessions[session_id] = {
                "queries": [],
                "entities": [],
                "filters": {}
            }
        return self._sessions[session_id]

    def update_context(self, session_id: str, query: str, intent: str = None, entities: List[Any] = None, sql_executed: str = None) -> None:
        """Updates the session context with latest queries, intents, entities, and filters."""
        context = self.get_context(session_id)
        
        # 1. Maintain last 5 queries
        context["queries"].append(query)
        if len(context["queries"]) > 5:
            context["queries"].pop(0)

        # 2. Maintain entities
        if entities:
            if isinstance(entities, dict):
                flat_entities = []
                for val_list in entities.values():
                    if isinstance(val_list, list):
                        flat_entities.extend(val_list)
                    elif isinstance(val_list, str):
                        flat_entities.append(val_list)
                entities_list = flat_entities
            else:
                entities_list = entities

            # Accumulate entities without duplicates
            for entity in entities_list:
                if entity not in context["entities"]:
                    context["entities"].append(entity)
            # Cap entities at 15
            if len(context["entities"]) > 15:
                context["entities"] = context["entities"][-15:]

        # 3. Store active filter context
        if sql_executed:
            context["filters"]["last_sql"] = sql_executed
        if intent:
            context["filters"]["last_intent"] = intent

    def clear_context(self, session_id: str) -> None:
        """Resets the context for a session_id."""
        if session_id in self._sessions:
            self._sessions[session_id] = {
                "queries": [],
                "entities": [],
                "filters": {}
            }

session_manager = SessionManager()
