import http.client
import json
import os

# --- SENDER: LEXICONA (LEXC-74Q2-K1T8) ---
# --- SUBJECT: INDEPENDENT KEY VERIFICATION ---

def check_gemini_quota(api_key, model="gemini-1.5-flash", version="v1beta"):
    """
    Performs a direct, zero-proxy request to Google to verify 
    if the key is operational and determine its tier (Free vs PAYG).
    """
    # Remove 'models/' prefix if present for the path
    model_id = model[7:] if model.startswith("models/") else model

    print(f"\n[AUDIT] PROBING GOOGLE AI STUDIO ({version}, MODEL: {model_id})...")
    
    conn = http.client.HTTPSConnection("generativelanguage.googleapis.com")
    payload = json.dumps({
        "contents": [{"parts": [{"text": "Respond with 'FUEL_CHECK_OK'"}]}]
    })
    
    headers = {'Content-Type': 'application/json'}
    endpoint = f"/{version}/models/{model_id}:generateContent?key={api_key}"
    
    try:
        conn.request("POST", endpoint, payload, headers)
        response = conn.getresponse()
        status = response.status
        data = response.read().decode()
        
        if status == 200:
            print(f"✅ SUCCESS: Key is Operational ({status} OK)")
            # print(f"   Response: {json.loads(data)['candidates'][0]['content']['parts'][0]['text'].strip()}")
            print("   Verdict: Key is valid. If LiteLLM still fails, check proxy routing.")
            return True
        elif status == 429:
            print(f"❌ QUOTA EXHAUSTED ({status} Too Many Requests)")
            print("   Verdict: Key is valid, but Google has capped your daily usage.")
            print("   Action: Check Google Cloud Console to ensure Billing is actually attached.")
            return True
        elif status == 400:
            print(f"⚠️  BAD REQUEST ({status})")
            # print(f"   Error: {data}")
        elif status == 404:
            print(f"❓ NOT FOUND ({status}) - Model {model_id} on {version}")
        else:
            print(f"🚫 AUTH FAILURE ({status})")
            # print(f"   Error: {data}")
            
    except Exception as e:
        print(f"💥 CONNECTION ERROR: {str(e)}")
    finally:
        conn.close()
    return False

if __name__ == "__main__":
    KEY = "AIzaSyA8QiDW3Hy5Lew7JTd75X3iYk-W2OGw33w" 
    
    if KEY == "YOUR_API_KEY_HERE":
        print("Please edit verify_gemini_fuel.py and insert your API Key.")
    else:
        # Try models that were confirmed to exist in the list
        models = ["gemini-pro-latest", "gemini-flash-latest"]
        versions = ["v1beta", "v1"]
        
        found = False
        for m in models:
            for v in versions:
                if check_gemini_quota(KEY, m, v):
                    found = True
                    break
            if found: break
        
        if not found:
            print("\n❌ ALL PROBES FAILED. Key might be invalid or restricted.")
