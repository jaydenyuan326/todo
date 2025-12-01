# Todo Master - Advanced Task Management Pro

**Todo Master** is a desktop productivity application that transforms standard task management into an engaging, gamified experience. Built with Python and **CustomTkinter**, it replaces boring lists with a visual **Kanban Board** and rewards users with **XP (Experience Points)** for completing tasks.

Beyond the user interface, this project serves as a practical implementation of fundamental Computer Science concepts, featuring a custom **Doubly Linked List** backend and a **Merge Sort** algorithm built from scratch.

-----

## 📖 Table of Contents

- [Key Features](#-key-features)
- [Technical Architecture](#-technical-architecture)
- [Data Structures & Algorithms](#-data-structures--algorithms)
- [Installation](#-installation)
- [Usage Guide](#-usage-guide)
- [File Structure](#-file-structure)

-----

## ✨ Key Features

1.  **Kanban Workflow**:
    - Visualizes tasks in three columns: **To Do**, **In Progress**, and **Done**.
    - Tasks move through the pipeline via interactive buttons.

2.  **Gamification System**:
    - Earn **XP** by completing tasks.
    - **Dynamic Rewards**: High Priority tasks grant **100 XP**, Medium **50 XP**, and Low **20 XP**.
    - Leveling system tracks your long-term productivity.

3.  **Focus Tools**:
    - Integrated **Pomodoro Timer** (25-minute sessions).
    - Completing a focus session rewards bonus XP.

4.  **Smart Notifications**:
    - A background service (running on a separate thread) monitors task deadlines.
    - Sends system popup notifications when a task is due without freezing the app.

5.  **Data Persistence**:
    - Automatically saves all tasks, status, and user XP to a local `JSON` file upon exit.
    - Restores the exact state when the application is relaunched.

-----

## 🛠 Technical Architecture

- **Language**: Python 3
- **GUI Framework**: `CustomTkinter` (Modern, Dark-mode native UI)
- **Concurrency**: Python `threading` module for non-blocking notification monitoring.
- **Persistence**: JSON serialization/deserialization.
- **Notifications**: `plyer` library for cross-platform system alerts.

-----

## 🧠 Data Structures & Algorithms

Unlike standard Python applications that rely on built-in lists, this project implements its own backend logic to demonstrate algorithmic proficiency.

### 1. Doubly Linked List (Backend Storage)

Instead of an array, tasks are stored as nodes in a custom `TaskList` class.

- **Node Structure**: Each `TaskNode` contains data (description, priority, due date) and pointers (`next`, `prev`).
- **Why?** 
    - Enables **O(1) deletion** efficiency when a node reference is known (e.g., removing a task from the board).
    - Facilitates efficient bidirectional traversal tailored for the Kanban movement logic.

### 2. Merge Sort (Sorting Mechanism)

When the user selects **"Sort By Priority"**, the application triggers a custom Merge Sort algorithm.

- **Implementation**:
    1.  **Split**: Uses the **"Tortoise and Hare"** (slow/fast pointers) technique to find the middle of the linked list.
    2.  **Merge**: Recursively sorts and merges the sub-lists based on priority or due date.
- **Why?**
    - Linked lists lack random access, making Quick Sort inefficient. Merge Sort provides stable, sequential sorting with **O(N log N)** time complexity.

-----

## 🚀 Installation

### Prerequisites

- Python 3.10 or higher.

### Steps

1.  **Clone the repository** (or download the source code):

    ```bash
    git clone [https://github.com/your-username/todo-master.git](https://github.com/your-username/todo-master.git)
    cd todo-master
    ```

2.  **Install dependencies**:
    This project requires `customtkinter` for the GUI and `plyer` for notifications.

    ```bash
    pip install customtkinter plyer
    ```

3.  **Run the application**:

    ```bash
    python todo_master.py
    ```

-----

## 📖 Usage Guide

1.  **Create a Task**: Use the sidebar to enter a description, select a priority (High/Medium/Low), and optionally set a due date (YYYY-MM-DD). Click **"+ Add Task"**.
2.  **Manage Tasks**:
    - Click **"Start ▶"** to move a task from *To Do* to *In Progress*.
    - Click **"Done ✔"** to complete it and earn XP.
    - Click **"Delete 🗑"** to remove finished tasks.
3.  **Sort Tasks**: Use the dropdown in the bottom left to sort your board by **Priority** or **Due Date**.
4.  **Focus**: Click **"Start"** on the Pomodoro timer to begin a 25-minute work session.

-----

## 📂 File Structure

- **`todo_master.py`**: The main entry point containing all logic:
    - `TaskNode`: Data class for individual tasks.
    - `TaskList`: The Doubly Linked List implementation.
    - `NotificationService`: Threaded background worker.
    - `App`: The CustomTkinter GUI controller.
- **`todo_data.json`**: Automatically generated file used to store your tasks and XP data.

-----

### Author

Developed as a final project for **Data Structures and Algorithm Analysis**.
Demonstrates the practical application of linked data structures in software engineering.
