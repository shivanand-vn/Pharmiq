import threading

def async_db_call(master, target_func, args=(), success_callback=None, error_callback=None):
    """
    Executes a database call in a background thread to prevent UI freezing.
    Returns the result to the main UI thread via master.after().
    
    :param master: The root or frame widget that has the `.after` method
    :param target_func: The database function to run
    :param args: Tuple of arguments for the target_func
    :param success_callback: Function to call on success, receives the result
    :param error_callback: Function to call on error, receives the Exception object
    """
    def task():
        try:
            result = target_func(*args)
            if success_callback:
                # Schedule success on the main thread
                master.after(0, success_callback, result)
        except Exception as e:
            if error_callback:
                # Schedule error on the main thread
                master.after(0, error_callback, e)
            else:
                print(f"[Async DB Error] {target_func.__name__}: {e}")

    thread = threading.Thread(target=task, daemon=True)
    thread.start()
