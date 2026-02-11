import subprocess
import sys
import time
import os
import psutil

def get_process_tree_usage(root_proc):
    """Sum CPU and Memory for process and all children"""
    total_cpu = 0.0
    total_mem = 0.0
    procs = [root_proc]
    try:
        procs.extend(root_proc.children(recursive=True))
    except psutil.NoSuchProcess:
        pass
        
    for p in procs:
        try:
            # interval=0.0 is non-blocking, returns since last call
            # We will handle interval in the main loop
            total_cpu += p.cpu_percent(interval=None) 
            total_mem += p.memory_info().rss
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
            
    return total_cpu, total_mem, len(procs)

def monitor_cpu(pid, duration=10):
    try:
        root_proc = psutil.Process(pid)
        cpu_count = os.cpu_count() or 1
        
        print(f"Monitoring PID {pid} Tree")
        print(f"Command: {' '.join(root_proc.cmdline())}")
        print(f"Logical CPUs: {cpu_count}")
        print("-" * 75)
        print(f"{'Time':<8} | {'Tree CPU %':<12} | {'Tree Mem (MB)':<14} | {'Process Count':<14}")
        print("-" * 75)
        
        # Initial seeding for all processes
        get_process_tree_usage(root_proc)
        
        start_time = time.time()
        
        while time.time() - start_time < duration:
            # We sleep here manually to create the interval
            time.sleep(1.0)
            
            elapsed = int(time.time() - start_time)
            
            try:
                # Re-fetch children every time in case new ones spawn
                # Note: cpu_percent(interval=None) compares to last call.
                # Since we sleep 1.0s, the diff is over 1.0s.
                
                # However, for new children, first call returns 0.0. 
                # This is acceptable error for this simple script.
                
                cpu_p, mem_b, count = get_process_tree_usage(root_proc)
                
                # Normalize to system total
                system_total = cpu_p / cpu_count
                mem_mb = mem_b / 1024 / 1024
                
                print(f"{elapsed:<8} | {system_total:<12.4f} | {mem_mb:<14.2f} | {count:<14}")
                
                if not root_proc.is_running():
                    print("Root process exited.")
                    break
            except psutil.NoSuchProcess:
                print("Root process exited.")
                break
                
    except Exception as e:
        print(f"Monitoring failed: {e}")

def main():
    exe_path = os.path.join("dist", "ShazamLive.exe")
    print(f"Launching '{exe_path}'...")
    
    try:
        if sys.platform == 'win32':
            creation_flags = subprocess.CREATE_NEW_CONSOLE
        else:
            creation_flags = 0
            
        proc = subprocess.Popen([exe_path], 
                                creationflags=creation_flags)
        
        print(f"Launched with PID: {proc.pid}")
        print("Waiting 3 seconds...")
        time.sleep(3)
        
        monitor_cpu(proc.pid, duration=10)
        
        print("\nBenchmark complete.")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
