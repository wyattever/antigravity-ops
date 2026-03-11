import litellm
from litellm.integrations.custom_logger import CustomLogger
import os
import json
import psycopg2
from datetime import datetime

print("ACP-LOGGER-INIT: ACPCustomLogger handler module loaded")

class ACPCustomLogger(CustomLogger):
    """
    ACP Phase 3: PostgreSQL Telemetry Handler
    Intercepts X-AND-TRACE and X-AND-SESSION headers for sovereign logging.
    """
    def log_pre_api_call(self, model, messages, kwargs, print_verbose):
        print(f"DEBUG-ACP: Calling model {model} (pre-api)")

    def log_post_api_call(self, kwargs, response_obj, start_time, end_time):
        pass

    def log_success_event(self, kwargs, response_obj, start_time, end_time):
        """
        Triggered on successful LLM responses.
        Captures metadata and traces to the existing LiteLLM Postgres table.
        """
        try:
            print(f"DEBUG-ACP: kwargs keys: {list(kwargs.keys())}")
            litellm_params = kwargs.get("litellm_params", {})
            print(f"DEBUG-ACP: litellm_params keys: {list(litellm_params.keys())}")
            
            proxy_req = litellm_params.get("proxy_server_request") or kwargs.get("call_kwargs", {})
            headers = {}
            if hasattr(proxy_req, 'get'):
                headers = proxy_req.get("headers", {})
            elif isinstance(proxy_req, dict):
                headers = proxy_req.get("headers", {})
            
            print(f"DEBUG-ACP: headers: {list(headers.keys()) if headers else 'None'}")
            
            trace_id = headers.get("X-AND-TRACE", headers.get("x-and-trace", "unknown-trace"))
            session_id = headers.get("X-AND-SESSION", headers.get("x-and-session", "unknown-session"))
            
            # Metadata for internal debugging
            metadata = litellm_params.get("metadata", {})
            metadata["acp_trace_id"] = trace_id
            metadata["acp_session_id"] = session_id

            tool_used = "chat"
            # Capture Tool Usage Telemetry
            if hasattr(response_obj, 'choices') and len(response_obj.choices) > 0:
                message = response_obj.choices[0].message
                if hasattr(message, 'tool_calls') and message.tool_calls:
                    tool_name = message.tool_calls[0].function.name
                    metadata["tool_used"] = tool_name
                    tool_used = tool_name
                    
                    # If tool is workspace_snapshot, extract commit hash if returned
                    # (Note: In Phase 4.5, commit hash comes from the tool result, not the LLM call)
                    # For now, we log the tool used. Commit hash will be tracked in agent_inbox.
                    print(f"ACP-TOOL: {tool_name} triggered for Session {session_id}")
            
            print(f"ACP Telemetry: Logged Trace {trace_id} for Session {session_id}")
            
            # Phase 4.5: DB Persistence for agent_inbox
            self._log_to_db(trace_id, session_id, tool_used, "SUCCESS")
            
        except Exception as e:
            print(f"ACP Telemetry Error: {str(e)}")

    def _log_to_db(self, trace_id, session_id, tool_used, status):
        """
        Inserts snapshot and tool traces into the agent_inbox table.
        """
        try:
            db_url = os.environ.get("DATABASE_URL")
            if not db_url:
                print("ACP-DB-ERROR: DATABASE_URL not set")
                return

            conn = psycopg2.connect(db_url)
            cur = conn.cursor()
            
            cur.execute(
                "INSERT INTO agent_inbox (trace_id, session_id, status) VALUES (%s, %s, %s)",
                (trace_id, session_id, f"{tool_used}:{status}")
            )
            
            conn.commit()
            print(f"ACP-DB-SUCCESS: Inserted {trace_id} into agent_inbox")
            cur.close()
            conn.close()
        except Exception as e:
            print(f"ACP-DB-INSERT-ERROR: {str(e)}")

    def log_failure_event(self, kwargs, response_obj, start_time, end_time):
        pass

    def async_log_success_event(self, kwargs, response_obj, start_time, end_time):
        try:
            # Extract custom headers (Async)
            litellm_params = kwargs.get("litellm_params", {})
            proxy_req = litellm_params.get("proxy_server_request") or kwargs.get("call_kwargs", {})
            headers = {}
            if hasattr(proxy_req, 'get'):
                headers = proxy_req.get("headers", {})
            elif isinstance(proxy_req, dict):
                headers = proxy_req.get("headers", {})

            trace_id = headers.get("X-AND-TRACE", headers.get("x-and-trace", "unknown-trace"))
            session_id = headers.get("X-AND-SESSION", headers.get("x-and-session", "unknown-session"))
            
            # Metadata for internal debugging
            metadata = litellm_params.get("metadata", {})
            metadata["acp_trace_id"] = trace_id
            metadata["acp_session_id"] = session_id

            tool_used = "chat"
            # Capture Tool Usage Telemetry (Async)
            if hasattr(response_obj, 'choices') and len(response_obj.choices) > 0:
                message = response_obj.choices[0].message
                if hasattr(message, 'tool_calls') and message.tool_calls:
                    tool_name = message.tool_calls[0].function.name
                    metadata["tool_used"] = tool_name
                    tool_used = tool_name
                    print(f"ACP-TOOL (Async): {tool_name} triggered for Session {session_id}")
            
            print(f"ACP Telemetry (Async): Logged Trace {trace_id} for Session {session_id}")
            
            # Phase 4.5: DB Persistence (Async)
            self._log_to_db(trace_id, session_id, tool_used, "SUCCESS_ASYNC")
            
        except Exception as e:
            print(f"ACP Telemetry Error (Async): {str(e)}")


    async def async_post_call_success_hook(self, data, user_api_key_dict, response):
        """
        Avoid 500 error if LiteLLM calls this hook.
        """
        pass

# Register the callback globally for LiteLLM
proxy_custom_logger = ACPCustomLogger()
