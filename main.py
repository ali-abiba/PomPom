import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import time
import ctypes

# ---------------------------
# Task Management Module
# ---------------------------
class TaskManager:
    def __init__(self, filename='tasks.json'):
        self.filename = filename
        self.tasks = []
        self.load_tasks()

    def load_tasks(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r') as f:
                    self.tasks = json.load(f)
            except Exception as e:
                print("Error loading tasks:", e)
                self.tasks = []
        else:
            self.tasks = []

    def save_tasks(self):
        try:
            with open(self.filename, 'w') as f:
                json.dump(self.tasks, f)
        except Exception as e:
            print("Error saving tasks:", e)

    def add_task(self, description, pomos=1):
        task = {
            'id': int(time.time() * 1000),
            'description': description,
            'completed': False,
            'created': time.strftime("%Y-%m-%d %H:%M:%S"),
            'pomos': pomos,
            'completed_pomos': 0
        }
        self.tasks.append(task)
        self.save_tasks()

    def update_task(self, task_id, **kwargs):
        for task in self.tasks:
            if task['id'] == task_id:
                task.update(kwargs)
                self.save_tasks()
                break

    def delete_task(self, task_id):
        self.tasks = [task for task in self.tasks if task['id'] != task_id]
        self.save_tasks()

    def increment_completed_pomos(self, task_id):
        for task in self.tasks:
            if task['id'] == task_id:
                task['completed_pomos'] += 1
                if task['completed_pomos'] >= task['pomos']:
                    task['completed'] = True
                self.save_tasks()
                break

# ---------------------------
# Pomodoro Timer Module
# ---------------------------
class PomodoroTimer:
    def __init__(self, master, update_callback):
        self.master = master
        self.update_callback = update_callback
        self.work_duration = 25 * 60  # default: 25 minutes
        self.short_break_duration = 5 * 60  # default: 5 minutes
        self.long_break_duration = 15 * 60  # default: 15 minutes
        self.total_cycles = 4         # default: 4 cycles
        self.current_cycle = 0
        self.is_running = False
        self.timer_type = "work"  # work, short_break, long_break
        self.remaining_time = self.work_duration
        self.timer_id = None
        self.transition_timer = None  # New: for handling session transitions

    def start(self, timer_type="work"):
        if self.is_running:
            # If timer is running, cancel it first
            self.master.after_cancel(self.timer_id)
            self.is_running = False
        
        # Cancel any pending transition
        if self.transition_timer:
            self.master.after_cancel(self.transition_timer)
            self.transition_timer = None
        
        # Start the new timer
        self.is_running = True
        self.timer_type = timer_type
        if timer_type == "work":
            self.remaining_time = self.work_duration
        elif timer_type == "short_break":
            self.remaining_time = self.short_break_duration
        elif timer_type == "long_break":
            self.remaining_time = self.long_break_duration
        self.countdown()

    def pause(self):
        if self.is_running:
            self.master.after_cancel(self.timer_id)
            self.is_running = False
        if self.transition_timer:
            self.master.after_cancel(self.transition_timer)
            self.transition_timer = None

    def reset(self):
        if self.timer_id:
            self.master.after_cancel(self.timer_id)
        if self.transition_timer:
            self.master.after_cancel(self.transition_timer)
            self.transition_timer = None
        self.is_running = False
        self.current_cycle = 0
        self.timer_type = "work"
        self.remaining_time = self.work_duration
        self.update_callback(self.format_time(self.remaining_time), self.current_cycle, self.timer_type)

    def handle_session_end(self):
        if self.timer_type == "work":
            # End of a work session
            self.current_cycle += 1
            if self.current_cycle >= self.total_cycles:
                messagebox.showinfo("Pomodoro Timer", "All cycles completed!")
                self.reset()
                return
            else:
                # Start a break based on cycle count
                if self.current_cycle % 4 == 0:
                    self.timer_type = "long_break"
                    self.remaining_time = self.long_break_duration
                else:
                    self.timer_type = "short_break"
                    self.remaining_time = self.short_break_duration
        else:
            # End of a break session
            self.timer_type = "work"
            self.remaining_time = self.work_duration
        
        # Start the next session after a delay
        self.is_running = True
        self.countdown()

    def countdown(self):
        if self.remaining_time <= 0:
            # Update display to show 00:00
            self.update_callback(self.format_time(0), self.current_cycle, self.timer_type)
            
            # Schedule the next session after a delay (2 seconds)
            if self.transition_timer is None:  # Only schedule if not already scheduled
                self.transition_timer = self.master.after(2000, self.handle_session_end)
            return
        
        self.update_callback(self.format_time(self.remaining_time), self.current_cycle, self.timer_type)
        self.remaining_time -= 1
        self.timer_id = self.master.after(1000, self.countdown)

    def format_time(self, seconds):
        m, s = divmod(seconds, 60)
        return f"{m:02d}:{s:02d}"

    def update_settings(self, work_minutes, short_break_minutes, long_break_minutes, cycles):
        self.work_duration = work_minutes * 60
        self.short_break_duration = short_break_minutes * 60
        self.long_break_duration = long_break_minutes * 60
        self.total_cycles = cycles
        self.reset()

# ---------------------------
# Main Application
# ---------------------------
class ProductivityApp:
    def __init__(self, master):
        self.master = master
        master.title("Productivity App")
        
        # Add debounce timer
        self.settings_update_timer = None
        self.settings_debounce_delay = 1000  # 1 second delay

        # Add animation variables
        self.shake_animation_id = None
        self.shake_count = 0
        self.original_timer_pos = None
        self.is_timer_red = False

        # Set application icon
        try:
            import os
            icon_path = os.path.abspath("icon.ico")
            if os.path.exists(icon_path):
                print(f"Found icon at: {icon_path}")
                # Get the window handle
                hwnd = master.winfo_id()
                # Load the icon
                icon = ctypes.windll.user32.LoadImageW(0, icon_path, 1, 0, 0, 0x00000010)
                if icon:
                    # Set the icon for the window
                    ctypes.windll.user32.SendMessageW(hwnd, 0x0080, 0, icon)  # WM_SETICON
                    ctypes.windll.user32.SendMessageW(hwnd, 0x0080, 1, icon)  # WM_SETICON (small)
                    print("Icon set successfully")
                else:
                    print("Failed to load icon")
            else:
                print(f"Icon file not found at: {icon_path}")
        except Exception as e:
            print(f"Error in icon loading process: {str(e)}")

        # Define Theme
        self.theme = {
            "bg": "#1a1a1a",
            "fg": "#ffffff",
            "button_bg": "#2c3e50",
            "button_fg": "#ffffff",
            "entry_bg": "#2d2d2d",
            "list_bg": "#2d2d2d",
            "accent": "#3498db",
            "secondary": "#2c3e50"
        }

        # Initialize Task Manager
        self.task_manager = TaskManager()

        # Initialize Pomodoro Timer
        self.timer = PomodoroTimer(master, self.update_timer_display)

        # Build UI Components
        self.build_ui()
        # Load saved settings from file
        self.load_settings()

    def load_settings(self):
        """Load timer settings from a JSON file"""
        settings_file = 'timer_settings.json'
        if os.path.exists(settings_file):
            try:
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
                    self.work_entry.delete(0, tk.END)
                    self.work_entry.insert(0, str(settings.get('work_duration', 25)))
                    self.short_break_entry.delete(0, tk.END)
                    self.short_break_entry.insert(0, str(settings.get('short_break', 5)))
                    self.long_break_entry.delete(0, tk.END)
                    self.long_break_entry.insert(0, str(settings.get('long_break', 15)))
                    self.cycles_entry.delete(0, tk.END)
                    self.cycles_entry.insert(0, str(settings.get('cycles', 4)))
                    self.update_timer_settings()
            except Exception as e:
                print(f"Error loading settings: {e}")

    def save_settings(self):
        """Save timer settings to a JSON file"""
        settings = {
            'work_duration': int(self.work_entry.get()),
            'short_break': int(self.short_break_entry.get()),
            'long_break': int(self.long_break_entry.get()),
            'cycles': int(self.cycles_entry.get())
        }
        try:
            with open('timer_settings.json', 'w') as f:
                json.dump(settings, f)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def build_ui(self):
        self.master.configure(bg=self.theme["bg"])

        # Create frames for tasks and timer
        self.left_frame = tk.Frame(self.master, bg=self.theme["bg"])
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20, pady=20)
        self.right_frame = tk.Frame(self.master, bg=self.theme["bg"])
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=20, pady=20)

        # --- Left Frame: Task Panel ---
        task_title = tk.Label(self.left_frame, text="Tasks", bg=self.theme["bg"],
                              fg=self.theme["accent"], font=("Segoe UI", 28, "bold"))
        task_title.pack(pady=(0, 15))

        # Customizable Task View: Filter Options with modern styling
        filter_frame = tk.Frame(self.left_frame, bg=self.theme["bg"])
        filter_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(filter_frame, text="Filter:", bg=self.theme["bg"],
                 fg=self.theme["fg"], font=("Segoe UI", 11)).pack(side=tk.LEFT)
        
        self.filter_var = tk.StringVar()
        self.filter_var.set("All")
        
        # Create custom dropdown button
        self.filter_button = tk.Button(filter_frame, 
                                     textvariable=self.filter_var,
                                     bg=self.theme["entry_bg"],
                                     fg=self.theme["fg"],
                                     font=("Segoe UI", 11),
                                     relief=tk.FLAT,
                                     padx=10,
                                     pady=5,
                                     command=self.toggle_filter_menu)
        self.filter_button.pack(side=tk.LEFT, padx=5)
        
        # Create dropdown menu
        self.filter_menu = tk.Menu(self.master, 
                                 tearoff=0,
                                 bg=self.theme["entry_bg"],
                                 fg=self.theme["fg"],
                                 activebackground=self.theme["accent"],
                                 activeforeground=self.theme["button_fg"],
                                 font=("Segoe UI", 11),
                                 relief=tk.FLAT,
                                 borderwidth=0,
                                 selectcolor=self.theme["entry_bg"])
        
        # Add options to menu
        for option in ["All", "Active", "Completed"]:
            self.filter_menu.add_command(label=option,
                                       command=lambda opt=option: self.select_filter(opt))
        
        # Configure menu appearance
        self.filter_menu.configure(bg=self.theme["entry_bg"],
                                 fg=self.theme["fg"],
                                 activebackground=self.theme["accent"],
                                 activeforeground=self.theme["button_fg"],
                                 selectcolor=self.theme["entry_bg"],
                                 relief=tk.FLAT,
                                 borderwidth=0)
        
        # Bind hover effects
        self.filter_button.bind("<Enter>", lambda e: self.filter_button.configure(bg=self.theme["accent"]))
        self.filter_button.bind("<Leave>", lambda e: self.filter_button.configure(bg=self.theme["entry_bg"]))
        
        # Bind click outside to close menu
        self.master.bind("<Button-1>", self.close_filter_menu)
        
        # Create shadow frame for menu
        self.menu_shadow = tk.Frame(self.master, bg="#000000", height=2)
        self.menu_shadow.pack_forget()  # Hide initially

        # Task List with custom styling
        self.task_list_frame = tk.Frame(self.left_frame, bg=self.theme["list_bg"])
        self.task_list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Task Input Frame
        task_input_frame = tk.Frame(self.left_frame, bg=self.theme["bg"])
        task_input_frame.pack(fill=tk.X, pady=(0, 10))

        # Task Description Entry
        self.task_entry = tk.Entry(task_input_frame, bg=self.theme["entry_bg"],
                                   fg=self.theme["fg"], font=("Segoe UI", 11),
                                   insertbackground=self.theme["fg"],
                                   borderwidth=0,
                                   highlightthickness=0)
        self.task_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.task_entry.bind("<Return>", lambda event: self.add_task())

        # Pomos Entry
        pomos_frame = tk.Frame(task_input_frame, bg=self.theme["bg"])
        pomos_frame.pack(side=tk.RIGHT, padx=(5, 0))
        tk.Label(pomos_frame, text="Pomos:", bg=self.theme["bg"],
                 fg=self.theme["fg"], font=("Segoe UI", 11)).pack(side=tk.LEFT)
        self.pomos_entry = tk.Entry(pomos_frame, bg=self.theme["entry_bg"],
                                   fg=self.theme["fg"], font=("Segoe UI", 11),
                                   insertbackground=self.theme["fg"],
                                   width=5,
                                   borderwidth=0,
                                   highlightthickness=0)
        self.pomos_entry.pack(side=tk.LEFT)
        self.pomos_entry.insert(0, "1")
        
        # Add Task Button with modern styling
        add_task_button = tk.Button(self.left_frame, text="Add Task",
                                    command=self.add_task,
                                    bg=self.theme["accent"],
                                    fg=self.theme["button_fg"],
                                    font=("Segoe UI", 11, "bold"),
                                    relief=tk.FLAT,
                                    padx=20,
                                    pady=5)
        add_task_button.pack()

        # --- Right Frame: Pomodoro Timer & Settings ---
        timer_title = tk.Label(self.right_frame, text="Pomodoro Timer",
                               bg=self.theme["bg"], fg=self.theme["accent"],
                               font=("Segoe UI", 28, "bold"))
        timer_title.pack(pady=(0, 20))

        # Timer Display with modern styling
        self.focused_task_label = tk.Label(self.right_frame, text="", 
                                         font=("Segoe UI", 16),
                                         bg=self.theme["bg"], 
                                         fg=self.theme["fg"])
        self.focused_task_label.pack(pady=(0, 10))
        
        self.timer_label = tk.Label(self.right_frame, text="00:00", 
                                    font=("Segoe UI", 80, "bold"),
                                    bg=self.theme["bg"], 
                                    fg=self.theme["accent"])
        self.timer_label.pack(pady=20)

        # Timer Control Buttons with modern styling
        self.controls_frame = tk.Frame(self.right_frame, bg=self.theme["bg"])  # Change to instance variable
        self.controls_frame.pack(pady=20)
        
        button_style = {
            "font": ("Segoe UI", 11, "bold"),
            "relief": tk.FLAT,
            "padx": 20,
            "pady": 8
        }
        
        # Timer type buttons
        timer_types_frame = tk.Frame(self.controls_frame, bg=self.theme["bg"])
        timer_types_frame.pack(pady=(0, 10))
        
        start_pomo_button = tk.Button(timer_types_frame, text="Start Pomodoro",
                                     command=lambda: self.timer.start("work"),
                                     bg=self.theme["accent"],
                                     fg=self.theme["button_fg"],
                                     **button_style)
        start_pomo_button.pack(side=tk.LEFT, padx=5)
        
        start_short_break_button = tk.Button(timer_types_frame, text="Short Break",
                                            command=lambda: self.timer.start("short_break"),
                                            bg=self.theme["button_bg"],
                                            fg=self.theme["button_fg"],
                                            **button_style)
        start_short_break_button.pack(side=tk.LEFT, padx=5)
        
        start_long_break_button = tk.Button(timer_types_frame, text="Long Break",
                                           command=lambda: self.timer.start("long_break"),
                                           bg=self.theme["button_bg"],
                                           fg=self.theme["button_fg"],
                                           **button_style)
        start_long_break_button.pack(side=tk.LEFT, padx=5)
        
        # Control buttons
        control_buttons_frame = tk.Frame(self.controls_frame, bg=self.theme["bg"])
        control_buttons_frame.pack()
        
        pause_button = tk.Button(control_buttons_frame, text="Pause",
                                 command=self.timer.pause,
                                 bg=self.theme["button_bg"],
                                 fg=self.theme["button_fg"],
                                 **button_style)
        pause_button.pack(side=tk.LEFT, padx=5)
        
        reset_button = tk.Button(control_buttons_frame, text="Reset",
                                 command=self.timer.reset,
                                 bg=self.theme["button_bg"],
                                 fg=self.theme["button_fg"],
                                 **button_style)
        reset_button.pack(side=tk.LEFT, padx=5)

        # Timer Settings with modern styling
        settings_frame = tk.Frame(self.right_frame, bg=self.theme["bg"])
        settings_frame.pack(pady=20)
        
        label_style = {
            "bg": self.theme["bg"],
            "fg": self.theme["fg"],
            "font": ("Segoe UI", 11)
        }
        
        entry_style = {
            "bg": self.theme["entry_bg"],
            "fg": self.theme["fg"],
            "font": ("Segoe UI", 11),
            "width": 8,
            "relief": tk.FLAT,
            "insertbackground": self.theme["fg"],
            "borderwidth": 0,
            "highlightthickness": 0
        }
        
        # Work duration setting
        tk.Label(settings_frame, text="Work (min):", **label_style).grid(row=0, column=0, pady=5)
        self.work_entry = tk.Entry(settings_frame, **entry_style)
        self.work_entry.grid(row=0, column=1, pady=5)
        self.work_entry.insert(0, "25")
        self.work_entry.bind('<KeyRelease>', self.schedule_settings_update)
        
        # Short break duration setting
        tk.Label(settings_frame, text="Short Break (min):", **label_style).grid(row=1, column=0, pady=5)
        self.short_break_entry = tk.Entry(settings_frame, **entry_style)
        self.short_break_entry.grid(row=1, column=1, pady=5)
        self.short_break_entry.insert(0, "5")
        self.short_break_entry.bind('<KeyRelease>', self.schedule_settings_update)
        
        # Long break duration setting
        tk.Label(settings_frame, text="Long Break (min):", **label_style).grid(row=2, column=0, pady=5)
        self.long_break_entry = tk.Entry(settings_frame, **entry_style)
        self.long_break_entry.grid(row=2, column=1, pady=5)
        self.long_break_entry.insert(0, "15")
        self.long_break_entry.bind('<KeyRelease>', self.schedule_settings_update)
        
        # Cycles setting
        tk.Label(settings_frame, text="Cycles:", **label_style).grid(row=3, column=0, pady=5)
        self.cycles_entry = tk.Entry(settings_frame, **entry_style)
        self.cycles_entry.grid(row=3, column=1, pady=5)
        self.cycles_entry.insert(0, "4")
        self.cycles_entry.bind('<KeyRelease>', self.schedule_settings_update)

        self.populate_tasks()
        
        # Update window size after all widgets are placed
        self.master.update_idletasks()  # Ensure all widgets are rendered
        width = max(self.left_frame.winfo_reqwidth() + self.right_frame.winfo_reqwidth() + 80,
                   900)  # minimum width of 900
        height = max(self.left_frame.winfo_reqheight(),
                    self.right_frame.winfo_reqheight()) + 60
        self.master.geometry(f"{width}x{height}")

    def add_task(self):
        task_desc = self.task_entry.get().strip()
        try:
            pomos = int(self.pomos_entry.get())
            if pomos < 1:
                raise ValueError("Pomos must be at least 1")
        except ValueError:
            messagebox.showerror("Invalid input", "Please enter a valid number of pomos (minimum 1)")
            return

        if task_desc:
            self.task_manager.add_task(task_desc, pomos)
            self.task_entry.delete(0, tk.END)
            self.pomos_entry.delete(0, tk.END)
            self.pomos_entry.insert(0, "1")
            self.populate_tasks()

    def populate_tasks(self):
        # Clear existing tasks
        for widget in self.task_list_frame.winfo_children():
            widget.destroy()
            
        filter_option = self.filter_var.get()
        tasks = self.task_manager.tasks
        # Apply filtering based on selection
        if filter_option == "Active":
            tasks = [t for t in tasks if not t.get("completed", False)]
        elif filter_option == "Completed":
            tasks = [t for t in tasks if t.get("completed", False)]
        # Sort tasks by creation time
        tasks = sorted(tasks, key=lambda x: x.get("created", ""))
        for task in tasks:
            # Create a frame for each task row
            task_frame = tk.Frame(self.task_list_frame, bg=self.theme["list_bg"])
            task_frame.pack(fill=tk.X, padx=5, pady=2)
            
            # Status checkbox
            status = "[x] " if task.get("completed", False) else "[ ] "
            status_label = tk.Label(task_frame, text=status, bg=self.theme["list_bg"],
                                  fg=self.theme["fg"], font=("Segoe UI", 11))
            status_label.pack(side=tk.LEFT)
            
            # Task description
            pomos = task.get("pomos", 1)
            completed_pomos = task.get("completed_pomos", 0)
            pomo_status = f" ({completed_pomos}/{pomos})"
            task_text = task["description"] + pomo_status
            task_label = tk.Label(task_frame, text=task_text, bg=self.theme["list_bg"],
                                fg=self.theme["fg"], font=("Segoe UI", 11))
            task_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            # Buttons frame
            buttons_frame = tk.Frame(task_frame, bg=self.theme["list_bg"])
            buttons_frame.pack(side=tk.RIGHT)
            
            # Focus button
            focus_button = tk.Button(buttons_frame, text="Focus",
                                   command=lambda t=task: self.focus_task(t),
                                   bg=self.theme["accent"],
                                   fg=self.theme["button_fg"],
                                   font=("Segoe UI", 10),
                                   relief=tk.FLAT,
                                   padx=10,
                                   pady=2)
            focus_button.pack(side=tk.LEFT, padx=(0, 5))
            
            # Delete button
            delete_button = tk.Button(buttons_frame, text="×",
                                    command=lambda t=task: self.delete_task(t),
                                    bg=self.theme["list_bg"],
                                    fg="#e74c3c",  # Red color for delete button
                                    font=("Segoe UI", 14, "bold"),
                                    relief=tk.FLAT,
                                    padx=4,
                                    pady=0)
            delete_button.pack(side=tk.LEFT)
            
            # Bind hover effects
            focus_button.bind("<Enter>", lambda e, b=focus_button: b.configure(bg=self.theme["secondary"]))
            focus_button.bind("<Leave>", lambda e, b=focus_button: b.configure(bg=self.theme["accent"]))
            delete_button.bind("<Enter>", lambda e, b=delete_button: b.configure(fg="#c0392b"))  # Darker red on hover
            delete_button.bind("<Leave>", lambda e, b=delete_button: b.configure(fg="#e74c3c"))

    def shake_timer(self):
        if self.shake_count >= 10:
            self.shake_count = 0
            # Restore the timer in its original position
            self.timer_label.place_forget()
            self.timer_label.pack(in_=self.right_frame, after=self.focused_task_label, pady=20)
            self.original_timer_pos = None
            return

        # Store original position before first movement
        if self.original_timer_pos is None:
            self.original_timer_pos = (
                self.timer_label.winfo_x(),
                self.timer_label.winfo_y()
            )

        # Calculate offset based on shake count
        offset = 10 if self.shake_count % 2 == 0 else -10
        
        # Move the label using place while maintaining vertical position
        self.timer_label.place(x=self.original_timer_pos[0] + offset, 
                             y=self.original_timer_pos[1])
        
        self.shake_count += 1
        self.shake_animation_id = self.master.after(50, self.shake_timer)

    def set_timer_color(self, is_zero=False):
        """Update timer label color based on state"""
        if is_zero:
            self.timer_label.configure(fg="#e74c3c")  # Red color when timer hits zero
        else:
            self.timer_label.configure(fg=self.theme["accent"])  # Normal color

    def update_timer_display(self, time_str, cycle, timer_type):
        session_type = "Work" if timer_type == "work" else "Short Break" if timer_type == "short_break" else "Long Break"
        self.timer_label.config(text=time_str)
        
        # Check if timer is at zero
        if time_str == "00:00":
            self.set_timer_color(True)
            if self.shake_animation_id is None:
                # Store the current position before animation
                self.original_timer_pos = (
                    self.timer_label.winfo_x(),
                    self.timer_label.winfo_y()
                )
                self.timer_label.pack_forget()
                self.timer_label.pack(in_=self.right_frame, after=self.focused_task_label, before=self.controls_frame, pady=20)
                self.shake_timer()
        else:
            self.set_timer_color(False)
            if self.shake_animation_id is not None:
                self.master.after_cancel(self.shake_animation_id)
                self.shake_animation_id = None
                # Restore with original padding and position
                self.timer_label.place_forget()
                self.timer_label.pack(in_=self.right_frame, after=self.focused_task_label, before=self.controls_frame, pady=20)
        
        # Update window title with focused task info
        focused_task = self.focused_task_label.cget("text")
        if focused_task:
            self.master.title(f"Pomodoro Timer - Cycle {cycle+1}/{self.timer.total_cycles} ({session_type}) - {focused_task}")
        else:
            self.master.title(f"Pomodoro Timer - Cycle {cycle+1}/{self.timer.total_cycles} ({session_type})")
        
        # If this is the end of a work session, increment the completed pomos for the focused task
        if timer_type == "work" and self.timer.remaining_time == 0:
            focused_task = self.focused_task_label.cget("text")
            if focused_task:
                # Extract task description from focused task label
                task_desc = focused_task.replace("Focusing on: ", "").split(" (")[0]
                # Find and update the task
                for task in self.task_manager.tasks:
                    if task["description"] == task_desc:
                        self.task_manager.increment_completed_pomos(task['id'])
                        self.populate_tasks()
                        # Update focused task label with new pomo count
                        pomos = task.get("pomos", 1)
                        completed_pomos = task.get("completed_pomos", 0)
                        self.focused_task_label.config(text=f"Focusing on: {task['description']} ({completed_pomos}/{pomos} pomos)")
                        break

    def update_timer_settings(self):
        try:
            work_minutes = int(self.work_entry.get())
            short_break_minutes = int(self.short_break_entry.get())
            long_break_minutes = int(self.long_break_entry.get())
            cycles = int(self.cycles_entry.get())
            self.timer.update_settings(work_minutes, short_break_minutes, long_break_minutes, cycles)
            self.save_settings()  # Add this line
        except ValueError:
            messagebox.showerror("Invalid input", "Please enter valid numbers for timer settings.")

    def schedule_settings_update(self, event=None):
        # Cancel the previous timer if it exists
        if self.settings_update_timer is not None:
            self.master.after_cancel(self.settings_update_timer)
        
        # Schedule a new timer
        self.settings_update_timer = self.master.after(
            self.settings_debounce_delay, 
            self.update_timer_settings
        )

    def toggle_filter_menu(self, event=None):
        # Get button position
        x = self.filter_button.winfo_rootx()
        y = self.filter_button.winfo_rooty() + self.filter_button.winfo_height()
        
        # Show shadow frame
        self.menu_shadow.place(x=x, y=y+2)
        self.menu_shadow.configure(width=self.filter_button.winfo_width())
        self.menu_shadow.lift()
        
        # Show menu at button position
        self.filter_menu.post(x, y)
        
    def select_filter(self, option):
        self.filter_var.set(option)
        self.populate_tasks()
        self.close_filter_menu()
        
    def close_filter_menu(self, event=None):
        # Only close if click is outside the button and menu
        if event:
            x, y = event.x_root, event.y_root
            button_x = self.filter_button.winfo_rootx()
            button_y = self.filter_button.winfo_rooty()
            button_width = self.filter_button.winfo_width()
            button_height = self.filter_button.winfo_height()
            
            if not (button_x <= x <= button_x + button_width and
                   button_y <= y <= button_y + button_height):
                self.filter_menu.unpost()
                self.menu_shadow.place_forget()
        else:
            self.filter_menu.unpost()
            self.menu_shadow.place_forget()

    def focus_task(self, task):
        # Update the focused task label
        pomos = task.get("pomos", 1)
        completed_pomos = task.get("completed_pomos", 0)
        self.focused_task_label.config(text=f"Focusing on: {task['description']} ({completed_pomos}/{pomos} pomos)")
        
        # Update window title
        self.master.title(f"Pomodoro Timer - {task['description']} ({completed_pomos}/{pomos} pomos)")

    def delete_task(self, task):
        # If the task is currently focused, clear the focused task label and reset timer
        focused_task = self.focused_task_label.cget("text")
        if focused_task and task["description"] in focused_task:
            self.focused_task_label.config(text="")
            self.master.title("Pomodoro Timer")
            self.timer.reset()  # Reset the timer when focused task is deleted
        
        # Delete the task
        self.task_manager.delete_task(task['id'])
        self.populate_tasks()

if __name__ == "__main__":
    try:
        import os
        # Get the absolute path of the icon file
        icon_path = os.path.abspath("icon.ico")
        if os.path.exists(icon_path):
            # Set the taskbar icon for the entire application
            import ctypes
            myappid = 'mycompany.pompom.1.0' # arbitrary string
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception as e:
        print(f"Error setting app ID: {str(e)}")

    root = tk.Tk()
    
    try:
        # Set window icon
        root.iconbitmap(default="icon.ico")
    except Exception as e:
        print(f"Error setting window icon: {str(e)}")
        
    app = ProductivityApp(root)
    root.mainloop()
