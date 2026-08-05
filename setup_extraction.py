"""
===================================================================================
UCOE Extraction Setup Script
===================================================================================
This script prepares the environment for testing extraction on a given employer.
It performs the following:
  1. Resets extraction phases to 'not_started'
  2. Ensures documents have parse_status = 'completed' (ready for extraction)
  3. Grants the user's role edit access for ingestion & extraction (enables button)
  4. Removes stale canonical records from previous extractions
  5. Restarts the API Docker container with updated credentials & code

PREREQUISITES:
  - Docker is running with MongoDB container on port 27017
  - The alight-ucoe-api Docker image exists (alight-ucoe-api:local)
  - You are in the UCOE_onboarding-v1-service project root directory

USAGE:
  1. Update your AWS credentials in .env (lines 16-17):
       AWS_ACCESS_KEY_ID=<your-valid-key>
       AWS_SECRET_ACCESS_KEY=<your-valid-secret>

  2. Run this script from the project root:
       docker exec alight-ucoe-api python /app/setup_extraction.py

     OR if the container isn't running yet:
       python src/setup_extraction.py  (requires working local pymongo)

  3. Restart the container (script does this automatically if run with --restart):
       docker rm -f alight-ucoe-api 2>/dev/null
       docker run -d --name alight-ucoe-api --network host \
         --env-file .env \
         -e MONGODB_URI=mongodb://localhost:27017/alight_onboarding \
         -v "$(pwd)/src:/app" \
         alight-ucoe-api:local --port 9900

  4. Refresh the UI and click Extract!
===================================================================================
"""

import argparse
import os
import shutil
import subprocess
import sys
from datetime import datetime

from pymongo import MongoClient
from bson import ObjectId


# =================================================================================
# CONFIGURATION — Update these values for your employer/user
# =================================================================================
MONGO_URI = os.getenv("MONGODB_URI") or os.getenv("MONGO_URI") or "mongodb://localhost:27017"
DATABASE = os.getenv("MONGODB_DATABASE", "alight_onboarding")

# Employer to reset (get from URL: /employer/document-ingestion/<client_id>)
EMPLOYER_CLIENT_ID = "emp-35822be5ce97"

# Phases to reset
PHASES_TO_RESET = ["foundation", "configuration", "eligibility_grid"]

# User display name (partial match) — set to your name
USER_DISPLAY_NAME = "Charu Agarwal"
# =================================================================================


def connect_db():
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=10000)
    return client, client[DATABASE]


def reset_extraction_phases(db):
    """Reset extraction phases to not_started so Extract button triggers fresh extraction."""
    print("\n[1/4] Resetting extraction phases...")

    employer = db.employers.find_one({"client_id": EMPLOYER_CLIENT_ID})
    if not employer:
        print(f"  ERROR: Employer '{EMPLOYER_CLIENT_ID}' not found!")
        sys.exit(1)

    print(f"  Employer: {employer.get('display_name')} ({EMPLOYER_CLIENT_ID})")

    # Show current state
    extraction_phase = employer.get("extraction_phase", {})
    for phase in PHASES_TO_RESET:
        entry = extraction_phase.get(phase, {})
        print(f"    {phase}: {entry.get('status', 'N/A')}")

    # Collect canonical IDs to remove
    canonical_ids_to_remove = []
    for phase in PHASES_TO_RESET:
        entry = extraction_phase.get(phase, {})
        canonical_ids_to_remove.extend(entry.get("canonical_ids", []))

    # Reset phases
    update_fields = {}
    for phase in PHASES_TO_RESET:
        update_fields[f"extraction_phase.{phase}"] = {
            "status": "not_started",
            "reextract_status": "not_available",
            "summary": "",
            "error": "",
            "canonical_ids": [],
            "doc_ids": [],
            "updated_at": None,
        }

    db.employers.update_one(
        {"client_id": EMPLOYER_CLIENT_ID},
        {"$set": update_fields},
    )
    print("  ✓ Phases reset to 'not_started'")

    # Clean up canonical records
    if canonical_ids_to_remove:
        object_ids = []
        for cid in canonical_ids_to_remove:
            try:
                object_ids.append(ObjectId(cid))
            except Exception:
                object_ids.append(cid)
        result = db.canonical_model.delete_many({"_id": {"$in": object_ids}})
        print(f"  ✓ Removed {result.deleted_count} canonical records")
    else:
        # Fallback: delete by document_id
        doc_ids = [str(d["_id"]) for d in db.documents.find({"client_id": EMPLOYER_CLIENT_ID}, {"_id": 1})]
        if doc_ids:
            result = db.canonical_model.delete_many({"document_id": {"$in": doc_ids}})
            if result.deleted_count:
                print(f"  ✓ Removed {result.deleted_count} canonical records")


def ensure_documents_ready(db):
    """Ensure all documents are in 'completed' (parsed) state."""
    print("\n[2/4] Ensuring documents are parsed and ready...")

    result = db.documents.update_many(
        {"client_id": EMPLOYER_CLIENT_ID},
        {"$set": {"parse_status": "completed"}},
    )

    docs = list(db.documents.find({"client_id": EMPLOYER_CLIENT_ID}, {"file_name": 1, "parse_status": 1}))
    for doc in docs:
        print(f"    {doc.get('file_name')}: {doc.get('parse_status')}")
    print(f"  ✓ {len(docs)} document(s) ready for extraction")


def grant_extraction_access(db):
    """Grant the user's role edit access for ingestion and extraction screens."""
    print("\n[3/4] Granting extraction access...")

    # Find employer and user
    employer = db.employers.find_one({"client_id": EMPLOYER_CLIENT_ID})
    members = employer.get("members", [])

    # Find user
    user = db.users.find_one({
        "$or": [
            {"display_name": {"$regex": USER_DISPLAY_NAME, "$options": "i"}},
            {"name": {"$regex": USER_DISPLAY_NAME, "$options": "i"}},
            {"first_name": {"$regex": USER_DISPLAY_NAME.split()[0], "$options": "i"}},
        ]
    })

    if not user:
        print(f"  WARNING: User '{USER_DISPLAY_NAME}' not found. Skipping access update.")
        print("  You may need to update USER_DISPLAY_NAME in this script.")
        return

    user_id = str(user["_id"])
    user_name = user.get("display_name") or user.get("name") or user.get("email", "Unknown")
    print(f"  User: {user_name}")

    # Find member entry
    member_entry = next((m for m in members if m.get("user_id") == user_id), None)
    if not member_entry:
        print(f"  WARNING: User not found in employer members. Cannot update role.")
        return

    role_id = member_entry.get("role")
    try:
        role = db.roles.find_one({"_id": ObjectId(role_id)})
    except Exception:
        role = db.roles.find_one({"_id": role_id})

    if not role:
        print(f"  WARNING: Role '{role_id}' not found.")
        return

    print(f"  Role: {role.get('name', 'Unknown')}")

    # Update screen_access
    db.roles.update_one(
        {"_id": role["_id"]},
        {"$set": {
            "screen_access.documentIngestion": "edit",
            "screen_access.extraction": "edit",
            "screen_access.ingestion": "edit",
        }},
    )
    print("  ✓ Role updated: documentIngestion=edit, extraction=edit")


def restart_container():
    """Stop and restart the API container with fresh credentials."""
    print("\n[4/4] Restarting API container...")

    docker_bin = shutil.which("docker")
    if not docker_bin:
        print("  WARNING: Docker CLI not found in this runtime. Skipping container restart.")
        print("  Run restart from host shell if needed.")
        return

    subprocess.run([docker_bin, "rm", "-f", "alight-ucoe-api"], capture_output=True)
    result = subprocess.run(
        [
            docker_bin, "run", "-d",
            "--name", "alight-ucoe-api",
            "--network", "host",
            "--env-file", ".env",
            "-e", "MONGODB_URI=mongodb://localhost:27017/alight_onboarding",
            "-v", f"{subprocess.check_output(['pwd']).decode().strip()}/src:/app",
            "alight-ucoe-api:local",
            "--port", "9900",
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        print(f"  ✓ Container started: {result.stdout.strip()[:12]}")
        print("  Server running at http://localhost:9900")
    else:
        print("  WARNING: Container restart failed in this runtime.")
        print(f"  Details: {result.stderr.strip()}")
        print("  Continue by restarting from host shell manually if needed.")


def main():
    global EMPLOYER_CLIENT_ID, USER_DISPLAY_NAME

    parser = argparse.ArgumentParser(description="Setup extraction environment for testing")
    parser.add_argument("--restart", action="store_true", help="Also restart the Docker container")
    parser.add_argument("--employer", default=EMPLOYER_CLIENT_ID, help="Employer client_id")
    parser.add_argument("--user", default=USER_DISPLAY_NAME, help="User display name (partial match)")
    args = parser.parse_args()

    EMPLOYER_CLIENT_ID = args.employer
    USER_DISPLAY_NAME = args.user

    print("=" * 70)
    print("UCOE Extraction Setup")
    print(f"Employer: {EMPLOYER_CLIENT_ID}")
    print(f"User: {USER_DISPLAY_NAME}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    client, db = connect_db()

    reset_extraction_phases(db)
    ensure_documents_ready(db)
    grant_extraction_access(db)

    client.close()

    if args.restart:
        restart_container()
    else:
        print("\n[4/4] Container restart skipped (use --restart flag to include)")
        print("  If needed, restart manually:")
        print("    docker rm -f alight-ucoe-api")
        print('    docker run -d --name alight-ucoe-api --network host \\')
        print('      --env-file .env \\')
        print('      -e MONGODB_URI=mongodb://localhost:27017/alight_onboarding \\')
        print('      -v "$(pwd)/src:/app" \\')
        print('      alight-ucoe-api:local --port 9900')

    print("\n" + "=" * 70)
    print("✓ DONE! Next steps:")
    print("  1. Ensure your AWS keys are updated in .env (lines 16-17)")
    print("  2. Refresh the UI at http://localhost:5173")
    print("  3. Click 'Extract' on any phase to test")
    print("=" * 70)


if __name__ == "__main__":
    main()

 