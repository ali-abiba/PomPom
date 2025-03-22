# PomPom - Productivity Timer

A modern Pomodoro timer application with task management capabilities.

## Features

- Pomodoro timer with customizable work and break durations
- Task management with Pomodoro tracking
- Modern dark theme interface
- Focus mode for tasks
- Filter tasks by status (All, Active, Completed)

## Installation

### From Source

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python main.py
   ```

### From Executable

1. Download the latest release
2. Extract the zip file
3. Run `PomPom.exe`

## Usage

1. Add tasks using the input field at the bottom of the task list
2. Set the number of Pomodoros needed for each task
3. Click "Focus" on a task to track Pomodoros for it
4. Use the timer controls to start work sessions and breaks
5. The application will track completed Pomodoros for each task

## Timer Settings

- Work Duration: Default 25 minutes
- Short Break: Default 5 minutes
- Long Break: Default 15 minutes
- Cycles: Default 4 (long break after 4 work sessions)

## Building from Source

To create an executable:

```bash
python -m PyInstaller --name="PomPom" --icon=icon.ico --add-data="icon.ico;." --noconsole --onefile main.py
```

The executable will be created in the `dist` directory.
