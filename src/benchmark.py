import time
from orchestrator import run_orchestrator

tasks = [
    "Write a Python function to calculate the factorial of a number.",
    "Write a script that reverses a string and prints it.",
    "Create a function that checks if a string is a palindrome.",
    "Write a script to find the largest number in a list of integers.",
    "Write a function that prints the Fibonacci sequence up to 10."
]

successful_runs = 0
total_time = 0

for i, task in enumerate(tasks, 1):
    start = time.time()
    
    final_state = run_orchestrator(task)
    
    end = time.time()
    total_time += (end - start)
    
    if final_state.status == "completed":
        successful_runs += 1

# Calculate final metrics
success_rate = (successful_runs / len(tasks)) * 100
avg_time = total_time / len(tasks)

print("\n" + "="*40)
print(" 📊 FINAL RESUME METRICS 📊")
print("="*40)
print(f"Autonomous Success Rate: {success_rate:.1f}%")
print(f"Average Execution Speed: {avg_time:.2f} seconds per task")
print("="*40)