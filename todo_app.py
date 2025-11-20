#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import customtkinter as ctk
import json
import os
import threading
import time
from datetime import datetime
from typing import Optional, List

# Ensure plyer is installed for notifications
try:
    from plyer import notification
except ImportError:
    print("Warning: 'plyer' not found. Notifications will be disabled.")
    def notification(title, message, app_name, timeout):
        print(f"[NOTIFICATION] {title}: {message}")

# Set application appearance
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

# --- Data File Path ---
DATA_FILE = "todo_data.json" 

# ==========================================
# 1. BACKEND - DATA STRUCTURES
# ==========================================

class TaskNode:
    """Represents a node in the Double Linked List (a single task)."""
    
    def __init__(self, description: str, priority="medium", due_date=None, status="todo", xp_value=None):
        self.description = description
        # Status for Kanban: "todo", "doing", "done"
        self.status = status 
        self.priority = priority
        self.due_date = due_date
        self.tags = []
        # Calculate XP value based on priority if not provided
        self.xp_value = xp_value if xp_value is not None else {"high": 100, "medium": 50, "low": 20}.get(priority, 20)
        
        # Pointers for DLL
        self.next: Optional['TaskNode'] = None
        self.prev: Optional['TaskNode'] = None

    # --- JSON Serialization Methods ---
    def to_dict(self):
        """Converts node to a dictionary for storage."""
        return {
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'due_date': self.due_date,
            'xp_value': self.xp_value
        }

    @staticmethod
    def from_dict(data):
        """Creates a TaskNode instance from a dictionary."""
        return TaskNode(
            description=data['description'],
            priority=data['priority'],
            due_date=data['due_date'],
            status=data['status'],
            xp_value=data['xp_value']
        )

class TaskList:
    """Double Linked List implementation for task management, including Merge Sort."""
    
    def __init__(self):
        self.head: Optional[TaskNode] = None
        self.count = 0
    
    # --- Core CRUD Methods ---
    
    def add_task(self, description: str, priority="medium", due_date=None) -> TaskNode:
        """Adds a brand new task (node) to the end of the list."""
        new_task = TaskNode(description, priority, due_date) 
        self.add_task_node(new_task)
        return new_task

    def add_task_node(self, new_task: TaskNode):
        """Adds an existing TaskNode instance (used for loading data) to the end."""
        if self.head is None:
            self.head = new_task
        else:
            current = self.head
            while current.next:
                current = current.next
            current.next = new_task
            new_task.prev = current
        self.count += 1

    def delete_task_node(self, node: TaskNode):
        """Deletes the specified node object from the list."""
        if not node: return
        
        if node == self.head:
            self.head = node.next
            if self.head:
                self.head.prev = None
        else:
            if node.prev:
                node.prev.next = node.next
            if node.next:
                node.next.prev = node.prev
        self.count -= 1

    # --- Utility Methods ---
    
    def get_tasks_by_status(self, status: str) -> List[TaskNode]:
        """Filters tasks by status for the Kanban view."""
        tasks = []
        current = self.head
        while current:
            if current.status == status:
                tasks.append(current)
            current = current.next
        return tasks
    
    def get_all_tasks(self) -> List[TaskNode]:
        """Returns all tasks in the list, used for saving data."""
        tasks = []
        current = self.head
        while current:
            tasks.append(current)
            current = current.next
        return tasks

    # --- MERGE SORT LOGIC for Double Linked List ---
    
    def _split(self, head):
        """Splits the DLL into two halves using tortoise and hare algorithm."""
        slow = head
        fast = head.next
        while fast and fast.next:
            slow = slow.next
            fast = fast.next.next
        
        second_half = slow.next
        
        # Break the list in two
        if second_half:
            second_half.prev = None
        slow.next = None 
        
        return head, second_half

    def _merge(self, left, right, key):
        """Merges two sorted halves based on the comparison key."""
        
        def get_value(node):
            """Helper function to map the task node to a comparable value."""
            if key == "priority":
                # Map priority: High=3, Medium=2, Low=1
                return {"high": 3, "medium": 2, "low": 1}.get(node.priority, 0)
            elif key == "due_date":
                # Use due date string; default to a very late date if None
                return node.due_date if node.due_date else "9999-12-31" 
            return 0

        dummy = TaskNode("dummy_merge_head")
        tail = dummy

        while left and right:
            val_left = get_value(left)
            val_right = get_value(right)
            
            # Determine which node comes next based on the key
            if key == "priority":
                # Priority: Higher numerical value (High) comes first (Descending)
                if val_left >= val_right:
                    tail.next = left
                    left.prev = tail
                    left = left.next
                else:
                    tail.next = right
                    right.prev = tail
                    right = right.next
            else: # key == "due_date"
                # Due Date: Earlier date comes first (Ascending)
                if val_left <= val_right:
                    tail.next = left
                    left.prev = tail
                    left = left.next
                else:
                    tail.next = right
                    right.prev = tail
                    right = right.next

            tail = tail.next

        # Attach remaining nodes
        remaining = left if left else right
        if remaining:
            tail.next = remaining
            remaining.prev = tail

        # Return the actual head
        merged_head = dummy.next
        if merged_head:
            merged_head.prev = None
        return merged_head

    def merge_sort(self, head, key="priority"):
        """Recursive Merge Sort entry point for the list segment."""
        if not head or not head.next:
            return head
        
        left, right = self._split(head)
        
        left = self.merge_sort(left, key)
        right = self.merge_sort(right, key)
        
        return self._merge(left, right, key)

    def sort_by(self, key):
        """Public method to sort the entire list and update the head."""
        self.head = self.merge_sort(self.head, key)
        
        # Re-establish count
        self.count = 0
        current = self.head
        while current:
            self.count += 1
            current = current.next

# ==========================================
# 2. BACKGROUND SERVICE (Notifications)
# ==========================================

class NotificationService:
    def __init__(self, task_list: TaskList):
        self.task_list = task_list
        self.running = False
        self.thread = None

    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._check_loop, daemon=True)
            self.thread.start()

    def _check_loop(self):
        print("🔔 Notification Service Started...")
        while self.running:
            current = self.task_list.head
            # Check for due date every minute (approximated time)
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M") 
            
            while current:
                if current.due_date and current.status != "done":
                    # Simple check: if due_date string matches current time (down to the minute)
                    if current.due_date in now_str: 
                        notification.notify(
                            title='Task Due Alert',
                            message=f'Action required: {current.description}',
                            app_name='Todo Master',
                            timeout=10
                        )
                current = current.next
            
            time.sleep(60)

# ==========================================
# 3. FRONTEND - GUI
# ==========================================

class TaskCard(ctk.CTkFrame):
    """A card widget representing a single task on the Kanban board."""
    
    def __init__(self, master, task: TaskNode, update_callback):
        super().__init__(master, corner_radius=10, fg_color="transparent", border_width=2, border_color="#3E3E3E")
        self.task = task
        self.update_callback = update_callback

        p_color = {"high": "#FF5555", "medium": "#FFFF55", "low": "#55FF55"}.get(task.priority, "gray")
        # Priority indicator (color bar)
        self.indicator = ctk.CTkLabel(self, text="", width=10, height=80, fg_color=p_color, corner_radius=5)
        self.indicator.pack(side="left", padx=(5, 5), pady=5)

        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        self.lbl_title = ctk.CTkLabel(self.content_frame, text=task.description, font=("Arial", 14, "bold"), anchor="w")
        self.lbl_title.pack(fill="x")

        # Display the due date clearly
        self.lbl_due = ctk.CTkLabel(self.content_frame, text=f"📅 {task.due_date or 'No Date'}", font=("Arial", 10), text_color="gray", anchor="w")
        self.lbl_due.pack(fill="x")

        self.btn_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.btn_frame.pack(fill="x", pady=(5, 0))

        if task.status == "todo":
            ctk.CTkButton(self.btn_frame, text="Start ▶", width=60, height=24, command=self.move_next, fg_color="#4488FF").pack(side="right")
        elif task.status == "doing":
            ctk.CTkButton(self.btn_frame, text="Done ✔", width=60, height=24, command=self.move_next, fg_color="#44AA44").pack(side="right")
            ctk.CTkButton(self.btn_frame, text="◀ Back", width=60, height=24, command=self.move_prev, fg_color="#666666").pack(side="right", padx=5)
        elif task.status == "done":
            ctk.CTkButton(self.btn_frame, text="Delete 🗑", width=60, height=24, command=self.delete_me, fg_color="#AA4444").pack(side="right")

    def move_next(self):
        xp_gain = 0
        if self.task.status == "todo": 
            self.task.status = "doing"
        elif self.task.status == "doing": 
            self.task.status = "done"
            xp_gain = self.task.xp_value # Reward XP only upon completion
        self.update_callback(xp_gain=xp_gain)

    def move_prev(self):
        if self.task.status == "doing": 
            self.task.status = "todo"
        self.update_callback()

    def delete_me(self):
        self.task.status = "deleted"
        self.update_callback()

class KanbanColumn(ctk.CTkScrollableFrame):
    """A scrollable frame to hold TaskCards for a specific status."""
    
    def __init__(self, master, title, status_filter, task_list, update_cb):
        super().__init__(master, label_text=title)
        self.status_filter = status_filter
        self.task_list = task_list
        self.update_cb = update_cb
        self.refresh()

    def refresh(self):
        # Clear existing widgets
        for widget in self.winfo_children():
            widget.destroy()
        
        # Draw new TaskCards
        tasks = self.task_list.get_tasks_by_status(self.status_filter)
        for t in tasks:
            card = TaskCard(self, t, self.update_cb)
            card.pack(fill="x", pady=5, padx=5)

class App(ctk.CTk):
    """Main application window and controller."""
    
    def __init__(self):
        super().__init__()

        self.title("Advanced Todo Manager Pro")
        self.geometry("1100x700")
        
        # --- FIX: Check if data file exists BEFORE loading ---
        is_first_run = not os.path.exists(DATA_FILE)

        # Core Data Initialization
        self.task_list = TaskList()
        self.total_xp = 0
        
        # --- Data Persistence: Load data ---
        self.load_data()
        
        # --- FIX: Only add default tasks if it's the TRUE first run and the list is empty ---
        if self.task_list.count == 0 and is_first_run:
            self.task_list.add_task("Finish Data Structures Project", "high", "2025-11-20")
            self.task_list.add_task("Buy Groceries", "low")
            self.task_list.add_task("Read Documentation", "medium")

        # --- Window Closing Handler (for saving data) ---
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Start background services
        self.notifier = NotificationService(self.task_list)
        self.notifier.start()

        # Layout Configuration
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # === Left Sidebar ===
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        self.logo_label = ctk.CTkLabel(self.sidebar, text="TODO MASTER", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.pack(pady=20)

        # XP System Display
        self.xp_frame = ctk.CTkFrame(self.sidebar, fg_color="#2B2B2B")
        self.xp_frame.pack(fill="x", padx=10, pady=10)
        self.lbl_xp = ctk.CTkLabel(self.xp_frame, text="", font=("Arial", 12))
        self.lbl_xp.pack(pady=10)
        self.update_xp_display() # Display loaded XP

        # Pomodoro Timer Area
        self.pomodoro_frame = ctk.CTkFrame(self.sidebar)
        self.pomodoro_frame.pack(fill="x", padx=10, pady=20)
        ctk.CTkLabel(self.pomodoro_frame, text="🍅 Focus Timer").pack(pady=5)
        self.timer_label = ctk.CTkLabel(self.pomodoro_frame, text="25:00", font=("Monospace", 24))
        self.timer_label.pack(pady=5)
        self.btn_start_timer = ctk.CTkButton(self.pomodoro_frame, text="Start", command=self.start_pomodoro, height=24)
        self.btn_start_timer.pack(pady=10, padx=10)
        self.timer_running = False # State variable for timer

        # Quick Add Task Form
        ctk.CTkLabel(self.sidebar, text="New Task:").pack(pady=(20,0))
        self.entry_task = ctk.CTkEntry(self.sidebar, placeholder_text="Task description...")
        self.entry_task.pack(pady=5, padx=10)
        
        # --- NEW DATE INPUT (Enhanced User Experience) ---
        ctk.CTkLabel(self.sidebar, text="Due Date (YYYY-MM-DD):").pack(pady=(5,0))
        self.entry_due_date = ctk.CTkEntry(self.sidebar, placeholder_text="e.g. 2025-11-20 (Optional)")
        self.entry_due_date.pack(pady=5, padx=10)
        # --- END NEW DATE INPUT ---
        
        self.combo_pri = ctk.CTkComboBox(self.sidebar, values=["high", "medium", "low"])
        self.combo_pri.pack(pady=5, padx=10)
        ctk.CTkButton(self.sidebar, text="+ Add Task", command=self.add_new_task).pack(pady=10, padx=10)

        # --- Sort Control (Merge Sort Integration) ---
        ctk.CTkLabel(self.sidebar, text="Sort By:").pack(pady=(20,0))
        self.combo_sort = ctk.CTkComboBox(self.sidebar, 
                                          values=["Priority (High First)", "Due Date (Sooner First)"],
                                          command=self.sort_tasks)
        self.combo_sort.pack(pady=5, padx=10)
        self.combo_sort.set("Priority (High First)") # Set default sort

        # === Main Content Area (Kanban) ===
        self.main_area = ctk.CTkFrame(self, fg_color="transparent")
        self.main_area.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_area.grid_columnconfigure((0, 1, 2), weight=1)
        self.main_area.grid_rowconfigure(0, weight=1)

        # Kanban Columns
        self.col_todo = KanbanColumn(self.main_area, "📝 TO DO", "todo", self.task_list, self.refresh_ui)
        self.col_todo.grid(row=0, column=0, sticky="nsew", padx=5)

        self.col_doing = KanbanColumn(self.main_area, "⚡ IN PROGRESS", "doing", self.task_list, self.refresh_ui)
        self.col_doing.grid(row=0, column=1, sticky="nsew", padx=5)

        self.col_done = KanbanColumn(self.main_area, "✅ DONE", "done", self.task_list, self.refresh_ui)
        self.col_done.grid(row=0, column=2, sticky="nsew", padx=5)
        
    # --- Data Persistence Methods ---
    
    def save_data(self):
        """Saves tasks and XP to the JSON file."""
        data = {
            'total_xp': self.total_xp,
            'tasks': [t.to_dict() for t in self.task_list.get_all_tasks()]
        }
        try:
            with open(DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
            print("💾 Data saved successfully.")
        except Exception as e:
            print(f"🚨 Error saving data: {e}")

    def load_data(self):
        """Loads tasks and XP from the JSON file."""
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.total_xp = data.get('total_xp', 0)
                
                # Rebuild the Double Linked List
                for task_data in data.get('tasks', []):
                    node = TaskNode.from_dict(task_data)
                    self.task_list.add_task_node(node)

                print("📦 Data loaded successfully.")
                
            except (json.JSONDecodeError, KeyError, FileNotFoundError) as e:
                print(f"⚠️ Error loading data: {e}. Starting with default data.")

    def on_closing(self):
        """Ensures data is saved and threads are stopped when the window closes."""
        self.save_data()
        if hasattr(self, 'timer_job'): # Check if timer_job exists before canceling
            self.after_cancel(self.timer_job) 
        self.notifier.running = False
        self.destroy()
        
    # --- UI & Controller Methods ---
    
    def sort_tasks(self, choice):
        """Triggers the Merge Sort on the DLL and refreshes the display."""
        
        if "Priority" in choice:
            key = "priority"
        elif "Due Date" in choice:
            key = "due_date"
        else:
            return

        # 1. Trigger the actual merge sort on the TaskList
        self.task_list.sort_by(key)
        
        # 2. Refresh the GUI to reflect the new order
        self.refresh_ui() 
        print(f"List sorted by: {key}")
    
    def update_xp_display(self):
        """Updates the Level and XP display label."""
        # Example: 500 XP per level
        level = 1 + self.total_xp // 500
        self.lbl_xp.configure(text=f"Level {level}\nXP: {self.total_xp}")

    def add_new_task(self):
        desc = self.entry_task.get()
        pri = self.combo_pri.get()
        # --- NEW: Get and clean the due date input ---
        due_date = self.entry_due_date.get().strip()
        if not due_date:
            due_date = None
        # --- END NEW ---

        if desc:
            self.task_list.add_task(desc, pri, due_date) # Pass due_date here
            self.entry_task.delete(0, "end")
            self.entry_due_date.delete(0, "end") # Clear the new date entry
            self.refresh_ui()

    def refresh_ui(self, xp_gain=0):
        """Updates XP and refreshes all Kanban columns."""
        # 1. Update XP
        if xp_gain > 0:
            self.total_xp += xp_gain
            self.update_xp_display()
        
        # 2. Handle deleted tasks (marked as "deleted" in the TaskNode)
        current = self.task_list.head
        while current:
            next_node = current.next
            if current.status == "deleted":
                self.task_list.delete_task_node(current)
            current = next_node

        # 3. Refresh Kanban columns
        self.col_todo.refresh()
        self.col_doing.refresh()
        self.col_done.refresh()

    # === Pomodoro Timer Logic ===
    def start_pomodoro(self):
        if hasattr(self, 'timer_running') and self.timer_running:
            return # Prevent multiple timers
            
        self.timer_seconds = 25 * 60 # 25 minutes
        self.btn_start_timer.configure(state="disabled")
        self.timer_running = True
        self.run_timer()

    def run_timer(self):
        if self.timer_seconds > 0:
            mins, secs = divmod(self.timer_seconds, 60)
            self.timer_label.configure(text=f"{mins:02d}:{secs:02d}")
            self.timer_seconds -= 1
            # Schedule the next call
            self.timer_job = self.after(1000, self.run_timer) 
        else:
            self.timer_running = False
            self.timer_label.configure(text="00:00")
            self.btn_start_timer.configure(state="normal", text="Start Again")
            
            # Send notification
            notification.notify(title="Pomodoro Finished", message="Focus time is over! Take a break.", app_name="Todo Master")
            
            # Reward XP for focus
            self.total_xp += 10
            self.refresh_ui()

if __name__ == "__main__":
    app = App()
    app.mainloop()