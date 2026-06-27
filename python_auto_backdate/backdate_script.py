import subprocess
from datetime import datetime, timedelta
import os
import time
import random

# Path configurations
script_dir = os.path.dirname(os.path.abspath(__file__))
repo_path = os.path.abspath(os.path.join(script_dir, ".."))
file_path = os.path.join(script_dir, "auto_backdate_file.py")

# Hard-coded start and end dates
start_date = datetime(2025, 5, 17)
end_date = datetime(2025, 7, 23)
commit_message = "auto-commit"

# Range of random commits per day (between 1 and 30)
min_commits_per_day = 1
max_commits_per_day = 30

def run_git_command(command):
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, cwd=repo_path)
        return result.returncode == 0, result.stdout.strip() or result.stderr.strip()
    except Exception as e:
        return False, str(e)

def get_git_config(config_name):
    success, output = run_git_command(f"git config {config_name}")
    return output if success else ""

# Fetch Git author details dynamically
author_name = get_git_config("user.name") or "UtkarshArora09"
author_email = get_git_config("user.email") or "utkarsharora09@users.noreply.github.com"

# Get local timezone offset (e.g. +0530 or -0400)
tz_offset_seconds = -time.timezone if time.daylight == 0 else -time.altzone
tz_hours = int(abs(tz_offset_seconds) / 3600)
tz_mins = int((abs(tz_offset_seconds) % 3600) / 60)
tz_sign = "+" if tz_offset_seconds >= 0 else "-"
tz_str = f"{tz_sign}{tz_hours:02d}{tz_mins:02d}"

print(f"Git Author: {author_name} <{author_email}>")
print(f"Timezone Offset: {tz_str}")

# Step 1: Ensure current files are saved in an initial commit
print("Staging current files...")
run_git_command("git add -A")
print("Creating initial setup commit...")
run_git_command('git commit -m "Initial setup commit"')
success, parent_sha = run_git_command("git rev-parse HEAD")


# Step 2: Generate the fast-import stream
print("Generating backdated commits stream...")
stream = []
current_date = start_date
day_counter = 0
total_commits = 0
commit_index = 0

while current_date <= end_date:
    backdate_str = current_date.strftime("%Y-%m-%d")
    num_commits = random.randint(min_commits_per_day, max_commits_per_day)
    total_commits += num_commits
    
    for i in range(num_commits):
        # Stagger commit times slightly (e.g. 12:00, 12:01, etc.)
        commit_time = current_date.replace(hour=12, minute=i % 60, second=0)
        epoch = int(commit_time.timestamp())
        
        stream.append("commit refs/heads/main")
        stream.append(f"author {author_name} <{author_email}> {epoch} {tz_str}")
        stream.append(f"committer {author_name} <{author_email}> {epoch} {tz_str}")
        msg = f"{commit_message} #{i+1} on {backdate_str}"
        msg_bytes = msg.encode("utf-8")
        stream.append(f"data {len(msg_bytes)}")
        stream.append(msg)
        
        if commit_index == 0:
            stream.append(f"from {parent_sha}")
        
        # Modify the backdate file in the first commit of the day
        if i == 0:
            if day_counter % 2 == 0:
                file_content = f"# We Will Do Our Backdating Edits Here\n#mcc {backdate_str}\n"
            else:
                file_content = f"# We Will Do Our Backdating Edits Here\n"
            file_content_bytes = file_content.encode("utf-8")
            stream.append("M 100644 inline python_auto_backdate/auto_backdate_file.py")
            stream.append(f"data {len(file_content_bytes)}")
            stream.append(file_content)
        
        stream.append("") # Separator between commits
        commit_index += 1

    current_date += timedelta(days=1)
    day_counter += 1

# Join stream into a single string
fast_import_data = "\n".join(stream)

# Step 3: Run git fast-import
print(f"Importing {total_commits} backdated commits via git fast-import...")
start_time = time.time()
try:
    process = subprocess.Popen(
        ["git", "fast-import"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=repo_path
    )
    stdout_bytes, stderr_bytes = process.communicate(input=fast_import_data.encode("utf-8"))
    stdout = stdout_bytes.decode("utf-8")
    stderr = stderr_bytes.decode("utf-8")
    
    if process.returncode == 0:
        elapsed = time.time() - start_time
        print(f"Success! Imported {total_commits} commits in {elapsed:.2f} seconds.")
    else:
        print(f"Error during import (code {process.returncode}):")
        print(f"stdout: {stdout}")
        print(f"stderr: {stderr}")
except Exception as e:
    print(f"Failed to run git fast-import: {e}")

# Step 4: Attempt to push all commits
print("\nAttempting to push all backdated commits to GitHub...")
success, push_output = run_git_command("git push -u origin main --force")
if success:
    print("All commits pushed successfully!")
else:
    print(f"Git push did not succeed. Output/Error:\n{push_output}")
