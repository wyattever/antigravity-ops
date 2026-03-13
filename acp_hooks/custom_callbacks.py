import litellm
from litellm.integrations.custom_logger import CustomLogger
import datetime
import os

class ACPInterceptor(CustomLogger):
    """
    Quiet Interceptor: Writes only verified hits to a dedicated authority.log file.
    """
    def log_to_file(self, entry):
        # Path is inside the mounted acp_hooks directory so it appears on the host
        log_path = "/app/acp_hooks/authority.log"
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open(log_path, "a") as f:
                f.write(f"[{timestamp}] {entry}\n")
        except Exception as e:
            print(f"[ACP-ERROR] Could not write to log: {str(e)}")

    async def async_log_success_event(self, kwargs, response_obj, start_time, end_time):
        try:
            user_message = kwargs.get("messages", [{}])[-1].get("content", "")
            litellm_params = kwargs.get("litellm_params", {})
            metadata = litellm_params.get("metadata", {}) or {}
            proxy_req = litellm_params.get("proxy_server_request") or {}
            
            # Extract headers robustly
            if isinstance(proxy_req, dict):
                headers = proxy_req.get("headers", {})
            elif hasattr(proxy_req, "headers"):
                headers = proxy_req.headers
            else:
                headers = getattr(proxy_req, "headers", {})
                
            # Convert headers to a case-insensitive dictionary equivalent (extract known keys safely)
            headers_dict = dict(headers) if hasattr(headers, "items") else {}
            
            # Hardened Search sequence: metadata -> headers -> X-Trace-ID -> X-AND-TRACE
            trace_id = (
                metadata.get("trace_id") or 
                metadata.get("trace-id") or 
                headers_dict.get("x-trace-id") or 
                headers_dict.get("X-Trace-ID") or 
                headers_dict.get("trace_id") or 
                headers_dict.get("X-AND-TRACE") or 
                headers_dict.get("x-and-trace") or 
                "unknown"
            )
            
            if "LEXC-VERIFY-999" in user_message or trace_id == "LEXC-VERIFY-999":
                log_entry = f"AUTHORITY_CONFIRMED | Model: {kwargs.get('model')} | Trace: {trace_id}"
                
                # Still print to stdout for safety, but with a unique prefix
                print(f"\n[ACP-RADAR] {log_entry}\n")
                
                # Write to the quiet log
                self.log_to_file(log_entry)
                
        except Exception:
            pass

# Initialize the interceptor
acp_interceptor = ACPInterceptor()
