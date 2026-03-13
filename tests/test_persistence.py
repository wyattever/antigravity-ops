from src.core.controller.mission_controller import MissionController, MissionState
from src.memory.context.session_store import SessionStore
import os
import json

def test_mission_persistence():
    print("🎬 Testing Antigravity Mission Persistence...")
    
    ag_home = os.environ.get('AG_HOME', os.path.expanduser('~/Agents'))
    db_path = os.path.join(ag_home, "antigravity-ops/memory/test_antigravity.db")
    if os.path.exists(db_path):
        os.remove(db_path)
        
    store = SessionStore(db_path=db_path)
    controller = MissionController(session_store=store)
    
    # 1. Create Mission
    objective = "Test Persistence Objective"
    mission_id = controller.create_mission(objective)
    print(f"🆔 Mission Created and Persisted: {mission_id}")
    
    # 2. Verify in DB
    loaded_mission = store.load_mission(mission_id)
    assert loaded_mission is not None
    assert loaded_mission["objective"] == objective
    print("✅ Mission verified in Database.")
    
    # 3. Simulate new controller instance (re-loading from DB)
    new_controller = MissionController(session_store=store)
    print("🧠 Decomposing mission using new controller instance...")
    plan = new_controller.decompose_task(mission_id)
    
    assert len(plan) > 0
    print(f"✅ Plan reconstructed from DB: {len(plan)} steps.")
    
    # 4. Verify History persistence
    print("🚀 Executing one step to test history persistence...")
    new_controller.execute_mission(mission_id) # This will execute the whole mission in our current simple implementation
    
    final_mission = store.load_mission(mission_id)
    assert final_mission["state"] == MissionState.COMPLETED
    assert len(final_mission["history"]) > 0
    print(f"✅ Mission History verified: {len(final_mission['history'])} entries.")
    print("🎉 Persistence verification complete.")

if __name__ == "__main__":
    test_mission_persistence()
