# main.py
import json
import os
import sys
import argparse
from orchestrator import build_graph
from state import ConversationalState
from initialization import create_initial_conversational_state

import random
from datetime import datetime

def create_checkpoint_directory():
    """Create checkpoints directory if it doesn't exist"""
    checkpoint_dir = "checkpoints"
    if not os.path.exists(checkpoint_dir):
        os.makedirs(checkpoint_dir)
    return checkpoint_dir

def save_chat_history_to_file(state, week_number, checkpoint_dir):
    """Save the chat history to a text file"""
    filename = f"week_{week_number:02d}_chat_history.txt"
    filepath = os.path.join(checkpoint_dir, filename)
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            # Write header
            f.write("=" * 80 + "\n")
            f.write("📋 COMPLETE CONVERSATION LOG\n")
            f.write("=" * 80 + "\n\n")
            
            chat_history = state.get('chat_history', [])
            if chat_history:
                for i, msg in enumerate(chat_history, 1):
                    sender = msg.get('agent') or msg.get('role', 'unknown')
                    text = msg.get('text', '')
                    timestamp = msg.get('timestamp')
                    
                    if timestamp:
                        # Parse ISO format string back to datetime for display
                        try:
                            dt = datetime.fromisoformat(timestamp)
                            time_str = dt.strftime("%a, %b %d, %I:%M %p")
                        except ValueError:
                            time_str = timestamp  # Fallback to raw string if parsing fails
                        f.write(f"{i:3d}. [{time_str}] [{sender.upper()}]: {text}\n")
                    else:
                        f.write(f"{i:3d}. [{sender.upper()}]: {text}\n")
            else:
                f.write("No conversations recorded.\n")
            
            f.write("\n" + "=" * 80 + "\n")
            
            # Write summary
            total_weeks = state.get('week_index', 0)
            active_decisions = len(state.get('active_decision_chains', []))
            completed_decisions = len(state.get('completed_decision_chains', []))
            
            f.write(f"\n=== SIMULATION SUMMARY ===\n")
            f.write(f"Completed {total_weeks} weeks with {len(chat_history)} total messages\n")
            f.write(f"Active events: {len(state.get('active_events', []))}, Completed: {len(state.get('completed_events', []))}\n")
            f.write(f"Decision chains - Active: {active_decisions}, Completed: {completed_decisions}\n")
            f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        print(f"💾 Chat history saved: {filename}")
        return True
    except Exception as e:
        print(f"❌ Failed to save chat history for week {week_number}: {e}")
        return False

def save_checkpoint(state, week_number, checkpoint_dir):
    """Save the current state to a checkpoint file"""
    filename = f"week_{week_number:02d}_checkpoint.json"
    filepath = os.path.join(checkpoint_dir, filename)
    
    # Create a serializable copy of the state
    checkpoint_data = {
        "week_number": week_number,
        "timestamp": datetime.now().isoformat(),
        "state": state
    }
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(checkpoint_data, f, indent=2, ensure_ascii=False)
        print(f"💾 Checkpoint saved: {filename}")
        return True
    except Exception as e:
        print(f"❌ Failed to save checkpoint for week {week_number}: {e}")
        return False

def load_checkpoint(week_number, checkpoint_dir):
    """Load state from a specific week checkpoint"""
    filename = f"week_{week_number:02d}_checkpoint.json"
    filepath = os.path.join(checkpoint_dir, filename)
    
    if not os.path.exists(filepath):
        print(f"❌ Checkpoint file not found: {filename}")
        return None
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            checkpoint_data = json.load(f)
        print(f"📂 Loaded checkpoint: {filename}")
        print(f"   Saved on: {checkpoint_data.get('timestamp', 'Unknown')}")
        return checkpoint_data.get('state')
    except Exception as e:
        print(f"❌ Failed to load checkpoint for week {week_number}: {e}")
        return None

def list_available_checkpoints(checkpoint_dir):
    """List all available checkpoint files"""
    if not os.path.exists(checkpoint_dir):
        return []
    
    checkpoints = []
    for filename in os.listdir(checkpoint_dir):
        if filename.startswith("week_") and filename.endswith("_checkpoint.json"):
            try:
                week_num = int(filename.split("_")[1])
                checkpoints.append(week_num)
            except (ValueError, IndexError):
                continue
    
    return sorted(checkpoints)

def get_user_choice_for_resume(auto_mode=False, auto_choice=None):
    """Ask user if they want to resume from a checkpoint or start fresh"""
    checkpoint_dir = "checkpoints"
    available_checkpoints = list_available_checkpoints(checkpoint_dir)
    
    if not available_checkpoints:
        print("No existing checkpoints found. Starting fresh simulation.")
        return None, None
    
    if auto_mode:
        # In automated mode, use the provided choice or default to latest checkpoint
        if auto_choice is not None:
            if auto_choice == 0:
                return None, None
            elif auto_choice in available_checkpoints:
                return auto_choice, checkpoint_dir
        
        # Default to latest checkpoint in auto mode
        latest = max(available_checkpoints)
        print(f"🤖 Auto mode: Resuming from latest checkpoint (week {latest})")
        return latest, checkpoint_dir
    
    print(f"\n📋 Available checkpoints: {available_checkpoints}")
    print("Options:")
    print("  0 - Start fresh simulation")
    for week in available_checkpoints:
        print(f"  {week} - Resume from week {week}")
    
    while True:
        try:
            choice = input("\nEnter your choice (0 for fresh start, or week number): ").strip()
            if choice == "0":
                return None, None
            
            week_num = int(choice)
            if week_num in available_checkpoints:
                return week_num, checkpoint_dir
            else:
                print(f"Invalid choice. Available weeks: {available_checkpoints}")
        except ValueError:
            print("Please enter a valid number.")
        except KeyboardInterrupt:
            print("\nExiting...")
            return None, None

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='35-Week Health Coaching Simulation with Checkpointing')
    parser.add_argument('--auto', action='store_true', 
                       help='Run in automatic mode (no user prompts)')
    parser.add_argument('--resume', type=int, metavar='WEEK',
                       help='Resume from specific week (0 for fresh start)')
    parser.add_argument('--max-weeks', type=int, default=35, metavar='N',
                       help='Maximum number of weeks to run (default: 35)')
    return parser.parse_args()

def main():
    # Parse command line arguments
    args = parse_arguments()
    
    # Initialize the conversation graph
    graph = build_graph()
    
    # Initialize checkpoint system
    checkpoint_dir = create_checkpoint_directory()
    
    # Initialize simulation (removed verbose startup messages)
    
    # Check for existing checkpoints and ask user if they want to resume
    resume_week, _ = get_user_choice_for_resume(auto_mode=args.auto, auto_choice=args.resume)
    
    if resume_week:
        # Load from checkpoint
        persistent_state = load_checkpoint(resume_week, checkpoint_dir)
        if persistent_state is None:
            print("Failed to load checkpoint. Starting fresh.")
            persistent_state = create_initial_conversational_state()
            start_week = 1
        else:
            start_week = resume_week + 1
    else:
        # Start fresh
        persistent_state = create_initial_conversational_state()
        start_week = 1
    
    # Outer loop: max_weeks (or from resume point)
    for week in range(start_week, args.max_weeks + 1):
        print(f"\n📅 WEEK {week} - Starting new week of conversation")
        print("-" * 40)
        
        # Update the week index in the persistent state
        persistent_state["week_index"] = week
        
        # Inner loop: 5 conversation threads per week (on average)
        threads_this_week = random.randint(2,4)  # Randomize between 3-5 threads per week
        
        for thread in range(1, threads_this_week + 1):
            print(f"\n💬 Thread {thread}/{threads_this_week} - Week {week}")
            print("-" * 30)
            
            # Update thread index and reset message counter for this thread
            persistent_state["thread_index"] = thread
            persistent_state["message_in_thread"] = 0
            
            # Create a copy of the current state for this thread execution
            thread_state = persistent_state.copy()
            
            try:
                # Execute this conversation thread
                for output in graph.stream(thread_state, config={"recursion_limit": 150}):
                    # The 'output' dictionary contains the state after each node has run
                    last_node = list(output.keys())[-1]
                    # Uncomment below if you want to see node execution details
                    # print(f"  Node '{last_node}' completed")
                
                # Get the final state after the thread is complete
                final_state = output[last_node]
                
                # Update the persistent state with the results from this thread
                # This ensures continuity across threads and weeks
                persistent_state.update(final_state)
                
            except Exception as e:
                print(f"  ❌ Error in thread {thread}: {e}")
                import traceback
                traceback.print_exc()
        
        # Save checkpoint after completing each week
        save_success = save_checkpoint(persistent_state, week, checkpoint_dir)
        
        # Save chat history to text file
        chat_save_success = save_chat_history_to_file(persistent_state, week, checkpoint_dir)
        
        if save_success and chat_save_success:
            print(f"Week {week} completed and saved successfully")
        elif save_success:
            print(f"Week {week} checkpoint saved but chat history save failed")
        else:
            print(f"Week {week} completed but checkpoint save failed")
            
    # Simulation complete - generate summary
    
    final_week = persistent_state.get('week_index', start_week - 1)
    total_weeks = final_week
    
    # Show checkpoint information
    available_checkpoints = list_available_checkpoints(checkpoint_dir)
    
    # Decision Tracking Summary
    active_decisions = len(persistent_state.get('active_decision_chains', []))
    completed_decisions = len(persistent_state.get('completed_decision_chains', []))
    print("\n=== SIMULATION SUMMARY ===")
    print(f"Completed {total_weeks} weeks with {len(persistent_state.get('chat_history', []))} total messages")
    print(f"Active events: {len(persistent_state.get('active_events', []))}, Completed: {len(persistent_state.get('completed_events', []))}")
    print(f"Decision chains - Active: {active_decisions}, Completed: {completed_decisions}")
    print(f"Checkpoints saved: {len(available_checkpoints)} weeks")
    
    # Save final comprehensive chat history
    final_chat_filename = f"final_complete_chat_history.txt"
    final_chat_filepath = os.path.join(checkpoint_dir, final_chat_filename)
    
    try:
        with open(final_chat_filepath, 'w', encoding='utf-8') as f:
            # Write header
            f.write("=" * 80 + "\n")
            f.write("📋 FINAL COMPLETE CONVERSATION LOG\n")
            f.write(f"35-Week Health Coaching Simulation Summary\n")
            f.write("=" * 80 + "\n\n")
            
            chat_history = persistent_state.get('chat_history', [])
            if chat_history:
                for i, msg in enumerate(chat_history, 1):
                    sender = msg.get('agent') or msg.get('role', 'unknown')
                    text = msg.get('text', '')
                    timestamp = msg.get('timestamp')
                    
                    if timestamp:
                        # Parse ISO format string back to datetime for display
                        try:
                            dt = datetime.fromisoformat(timestamp)
                            time_str = dt.strftime("%a, %b %d, %I:%M %p")
                        except ValueError:
                            time_str = timestamp  # Fallback to raw string if parsing fails
                        f.write(f"{i:3d}. [{time_str}] [{sender.upper()}]: {text}\n")
                    else:
                        f.write(f"{i:3d}. [{sender.upper()}]: {text}\n")
            else:
                f.write("No conversations recorded.\n")
            
            f.write("\n" + "=" * 80 + "\n")
            
            # Write comprehensive summary
            f.write(f"\n=== FINAL SIMULATION SUMMARY ===\n")
            f.write(f"Completed {total_weeks} weeks with {len(chat_history)} total messages\n")
            f.write(f"Active events: {len(persistent_state.get('active_events', []))}, Completed: {len(persistent_state.get('completed_events', []))}\n")
            f.write(f"Decision chains - Active: {active_decisions}, Completed: {completed_decisions}\n")
            f.write(f"Checkpoints saved: {len(available_checkpoints)} weeks\n")
            f.write(f"Simulation completed on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        print(f"💾 Final chat history saved: {final_chat_filename}")
    except Exception as e:
        print(f"❌ Failed to save final chat history: {e}")
    
    # Display all conversations
    print("\n" + "=" * 80)
    print("📋 COMPLETE CONVERSATION LOG")
    print("=" * 80)
    
    chat_history = persistent_state.get('chat_history', [])
    if chat_history:
        for i, msg in enumerate(chat_history, 1):
            sender = msg.get('agent') or msg.get('role', 'unknown')
            text = msg.get('text', '')
            timestamp = msg.get('timestamp')
            
            if timestamp:
                # Parse ISO format string back to datetime for display
                try:
                    dt = datetime.fromisoformat(timestamp)
                    time_str = dt.strftime("%a, %b %d, %I:%M %p")
                except ValueError:
                    time_str = timestamp  # Fallback to raw string if parsing fails
                print(f"{i:3d}. [{time_str}] [{sender.upper()}]: {text}")
            else:
                print(f"{i:3d}. [{sender.upper()}]: {text}")
    else:
        print("No conversations recorded.")
    
    print("=" * 80)

if __name__ == "__main__":
    main()