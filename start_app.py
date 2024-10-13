import os
import subprocess
import webbrowser
import customtkinter as ctk  # Using customTkinter for a modern UI
import tkinter as tk
import socket
import threading
import random
import time
import psutil  # For killing the server process properly
import re
import json
import sys
import requests
from pyngrok import ngrok, conf
from django.core.management import call_command
from django.conf import settings
from interface.db_handler import db
import atexit
from tkinter import messagebox

# Global variable to store the server process
server_process = None
root = None
error_window = None
smtp_host_var = None
smtp_port_var = None

# Get the current directory where the executable is running
base_dir = os.path.dirname(os.path.abspath(__file__))

def get_lan_ip():
    """Get the current LAN IP of the machine."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    return ip

def update_db(server_status, host, port, pid, smtp_host, smtp_port):
    """Update the database with the current server status, host, port, and SMTP settings."""
    db.set_value('SERVER_STATUS', server_status)
    db.set_value('LAN_IP', host)
    db.set_value('PORT', port)
    db.set_value('SERVER_PID', str(pid))
    db.set_value('SMTP_HOST', smtp_host)
    db.set_value('SMTP_PORT', smtp_port)
    db.set_value('NGROK_URL', os.environ.get('NGROK_URL', ''))

def flash_message(label, message, duration=2):
    """Display a message for a short time and then clear it."""
    label.configure(text=message)
    label.update()
    time.sleep(duration)
    label.configure(text="")

def handle_error(error_message, host, port, start_button, filling_button, open_button, close_button, port_entry, host_buttons, smtp_host_entry, smtp_port_entry, callback = None):
    update_title("Error")
    show_error_window(error_message, callback)
    stop_django(host, port, start_button, filling_button, open_button, close_button, port_entry, host_buttons, smtp_host_entry, smtp_port_entry)

def wait_for_url(process, regex_pattern, timeout=30):
    start_time = time.time()
    while time.time() - start_time < timeout:
        output = process.stdout.readline()
        match = re.search(regex_pattern, output)
        if match:
            return match.group(1)
    return None

def start_server(host, port):
    # Get the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Change to the Django project directory
    os.chdir(os.path.join(current_dir, 'interface'))
    
    # Run the Django server
    server_process = subprocess.Popen(
        [sys.executable, "manage.py", "runserver", f"{host}:{port}"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL, 
        stdin=subprocess.DEVNULL,
        start_new_session=True  
    )
    print(f"Attempting to start server at {host}:{port}")
    return server_process

def update_loader(target, speed, update_title_func):
    current = 0
    while current < target:
        current += speed
        if current > target:
            current = target
        update_title_func(f"Starting : {int(current)}%")
        time.sleep(0.01)

def start_django(host, port, start_button, filling_button, open_button, close_button, port_entry, host_buttons, smtp_host_entry, smtp_port_entry):
    global server_process
    
    print(f"[DEBUG] Starting Django server on {host}:{port}")

    loader_thread = None
    loader_target = 0
    loader_speed = 5

    def start_loader(target, speed):
        nonlocal loader_thread, loader_target, loader_speed
        loader_target = target
        loader_speed = speed 
        if loader_thread is None or not loader_thread.is_alive():
            loader_thread = threading.Thread(target=update_loader, args=(target, speed, update_title))
            loader_thread.start()
        else:
            loader_speed = speed

    start_loader(10, 0.5)  # Start loader at 0%, aiming for 10%

    # Change to the Django project directory
    os.chdir(os.path.join(base_dir, 'interface'))
    
    start_loader(30, 1)  # Update loader to aim for 30%

    url_to_open = None

    if host == "ngrok":
        print("[DEBUG] Using ngrok")
        start_loader(30, 1)  # Update loader to aim for 30%

        try:
            # Fetch Ngrok auth token from the database
            ngrok_auth_token = db.get_value('NGROK_AUTH_TOKEN', '')
            
            if not ngrok_auth_token:
                raise Exception("Ngrok auth token is not set. Please configure it in the settings.")

            # Set the auth token for this session
            ngrok.set_auth_token(ngrok_auth_token)

            # Start ngrok tunnel
            tunnel = ngrok.connect(port)
            
            if tunnel:
                url_to_open = tunnel.public_url
                print(f"Public URL: {url_to_open}")
                
                # Update the database with the public URL
                db.set_value('NGROK_URL', url_to_open)
                os.environ["NGROK_URL"] = url_to_open

                # Now start the Django server
                server_process = start_server('127.0.0.1', port)
                
                update_title(f"Running on {url_to_open}")
            else:
                raise Exception("Failed to start ngrok tunnel")

        except Exception as e:
            start_loader(100, 1)
            error_message = f"Error : {str(e)}"
            handle_error(error_message, host, port, start_button, filling_button, open_button, close_button, port_entry, host_buttons, smtp_host_entry, smtp_port_entry, update_ui_elements(start_button, filling_button, open_button, close_button, port_entry, host_buttons, smtp_host_entry, smtp_port_entry, False))
            return
    else:
        print(f"[DEBUG] Starting Django server directly on {host}:{port}")
        server_process = start_server(host, port)
        url_to_open = f"http://{host}:{port}"
        update_title(f"Running on {url_to_open}")

    update_title(f"Running on {url_to_open}")
    # Open the URL in the default web browser after the process completes
    if url_to_open:
        print(f"[DEBUG] Opening URL: {url_to_open}")
        webbrowser.open(url_to_open)

    # Wait for loader to finish
    if loader_thread:
        loader_thread.join()

    print("[DEBUG] Updating UI elements")
    # Update UI elements
    root.after(0, lambda: update_ui_after_start(open_button, close_button, start_button, filling_button, port_entry, host_buttons, smtp_host_entry, smtp_port_entry))

    print("[DEBUG] Updating database")
    # Update database
    update_db('running', host, port, str(server_process.pid), smtp_host_entry.get(), smtp_port_entry.get())

    print("[DEBUG] Django server start process completed")
    return host, port, str(server_process.pid), smtp_host_entry.get(), smtp_port_entry.get()

def update_ui_after_start(open_button, close_button, start_button, filling_button, port_entry, host_buttons, smtp_host_entry, smtp_port_entry):
    open_button.configure(state=ctk.NORMAL)
    close_button.configure(state=ctk.NORMAL)
    start_button.grid_forget()
    filling_button.grid_forget()
    open_button.grid(row=1, column=0, sticky="ew", padx=10, columnspan=1, pady=10)
    close_button.grid(row=1, column=1, sticky="ew", padx=10, columnspan=1, pady=10)
    port_entry.configure(state=ctk.DISABLED)
    for btn in host_buttons:
        btn.configure(state=ctk.DISABLED)
    smtp_host_entry.configure(state=ctk.DISABLED)
    smtp_port_entry.configure(state=ctk.DISABLED)

    # Remove this line as we're now updating the database in start_django
    # update_db('running', *server_info)

def update_ui_elements(start_button, filling_button, open_button, close_button, port_entry, host_buttons, smtp_host_entry, smtp_port_entry, is_starting):
    if is_starting:
        open_button.configure(state=ctk.NORMAL)
        close_button.configure(state=ctk.NORMAL)
        start_button.grid_forget()
        filling_button.grid_forget()
        open_button.grid(row=1, column=0, sticky="ew", padx=10, columnspan=1, pady=10)
        close_button.grid(row=1, column=1, sticky="ew", padx=10, columnspan=1, pady=10)
    else:
        start_button.configure(state=ctk.NORMAL)
        start_button.grid(row=1, column=1, sticky="ew", padx=10, columnspan=1, pady=10)
        filling_button.grid(row=1, column=0, sticky="ew", padx=10, columnspan=1, pady=10)
        open_button.grid_forget()
        close_button.grid_forget()
        
    update_title()
    port_entry.configure(state=ctk.DISABLED if is_starting else ctk.NORMAL)
    smtp_host_entry.configure(state=ctk.DISABLED if is_starting else ctk.NORMAL)
    smtp_port_entry.configure(state=ctk.DISABLED if is_starting else ctk.NORMAL)
    
    for btn in host_buttons:
        btn.configure(state=ctk.DISABLED if is_starting else ctk.NORMAL)

def stop_django(host, port, start_button, filling_button, open_button, close_button, port_entry, host_buttons, smtp_host_entry, smtp_port_entry):
    global server_process

    update_title("Stopping Server")
    if server_process is not None:
        parent_pid = server_process.pid
        parent_process = psutil.Process(parent_pid)

        for child in parent_process.children(recursive=True):
            child.terminate()
        parent_process.terminate()

        parent_process.wait()

        # If using ngrok, disconnect the tunnel and remove the URL from env
        if host == "ngrok":
            ngrok.disconnect(port)  # Disconnect the specific tunnel
            ngrok.kill()  # Kill the ngrok process

        server_process = None

        update_ui_elements(start_button, filling_button, open_button, close_button, port_entry, host_buttons, smtp_host_entry, smtp_port_entry, False)

        update_title()
        update_db('stopped', host, port, '', smtp_host_entry.get(), smtp_port_entry.get())

        # Remove the public URL from database
        if host == "ngrok":
            db.set_value('NGROK_URL', '')
            os.environ.pop("NGROK_URL", None)
    else:
        update_ui_elements(start_button, filling_button, open_button, close_button, port_entry, host_buttons, smtp_host_entry, smtp_port_entry, False)

    # Enable SMTP inputs
    smtp_host_entry.configure(state=ctk.NORMAL)
    smtp_port_entry.configure(state=ctk.NORMAL)

def update_title(status = None):
    global root
    if status == '' or status is None:
        root.title("Attacking Server")
    else:
        root.title(f"Attacking Server : {status}")

def show_error_window(message, callback=None):
    global error_window
    # Create a new top-level window
    error_window = tk.Toplevel(root)
    error_window.title("Error")
    error_window.geometry("400x200")
    error_window.resizable(False, False)
    
    # Create a label to display the error message
    error_label = tk.Label(error_window, text=message, wraplength=380)
    error_label.pack(pady=20, padx=20)
    
    # Create a frame for buttons
    button_frame = tk.Frame(error_window)
    button_frame.pack(side=tk.BOTTOM, pady=20)

    # Function to handle window close
    def on_close():
        error_window.destroy()
        if callback:
            callback()


    cancel_button = tk.Button(button_frame, text="Cancel", command=on_close)
    cancel_button.pack(side=tk.LEFT, padx=10)

    # Bind the window close event
    error_window.protocol("WM_DELETE_WINDOW", on_close)

    # Make the error window modal
    error_window.transient(root)
    error_window.grab_set()
    root.wait_window(error_window)

def open_settings_window():
    global root  # Make sure we have access to the main window

    settings_window = ctk.CTkToplevel(root)
    settings_window.title("Settings")
    settings_window.geometry("750x400")
    settings_window.resizable(True, True)

    # Make the settings window modal (blocks interaction with the main window)
    settings_window.grab_set()
    
    # Ensure the settings window stays on top of the main window
    settings_window.transient(root)

    # SMTP Settings Box
    smtp_frame = ctk.CTkFrame(settings_window)
    smtp_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
    ctk.CTkLabel(smtp_frame, text="SMTP Settings", font=("Arial", 16, "bold")).grid(row=0, column=0, columnspan=2, pady=10)

    smtp_fields = [
        ("SMTP Host:", "SMTP_HOST"),
        ("SMTP Port:", "SMTP_PORT"),
        ("SMTP Username:", "SMTP_USERNAME"),
        ("SMTP Password:", "SMTP_PASSWORD"),
    ]

    smtp_entries = {}
    for i, (label, key) in enumerate(smtp_fields):
        ctk.CTkLabel(smtp_frame, text=label, font=("Arial", 12)).grid(row=i+1, column=0, sticky="w", padx=10, pady=5)
        entry = ctk.CTkEntry(smtp_frame, width=200)
        entry.grid(row=i+1, column=1, padx=10, pady=5, sticky="ew")
        entry.insert(0, db.get_value(key, ''))
        smtp_entries[key] = entry

    # TLS/SSL/None option
    smtp_security_var = ctk.StringVar(value=db.get_value('SMTP_SECURITY', 'TLS'))
    ctk.CTkLabel(smtp_frame, text="Security:", font=("Arial", 12)).grid(row=len(smtp_fields)+1, column=0, sticky="w", padx=10, pady=5)
    security_frame = ctk.CTkFrame(smtp_frame)
    security_frame.grid(row=len(smtp_fields)+1, column=1, sticky="ew", padx=10, pady=5)
    ctk.CTkRadioButton(security_frame, text="TLS", variable=smtp_security_var, value="TLS").pack(side="left", padx=5, pady=5)
    ctk.CTkRadioButton(security_frame, text="SSL", variable=smtp_security_var, value="SSL").pack(side="left", padx=5, pady=5)
    ctk.CTkRadioButton(security_frame, text="None", variable=smtp_security_var, value="None").pack(side="left", padx=5, pady=5)

    # API Credentials Box
    api_frame = ctk.CTkFrame(settings_window)
    api_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
    ctk.CTkLabel(api_frame, text="API Credentials", font=("Arial", 16, "bold")).grid(row=0, column=0, columnspan=2, pady=10)

    api_fields = [
        ("Ngrok Auth Token:", "NGROK_AUTH_TOKEN"),
        ("Shodan API Key:", "SHODAN_API_KEY"),
    ]

    api_entries = {}
    for i, (label, key) in enumerate(api_fields):
        ctk.CTkLabel(api_frame, text=label, font=("Arial", 12)).grid(row=i*2+1, column=0, sticky="w", padx=10, pady=5)
        entry = ctk.CTkTextbox(api_frame, width=200, height=60)
        entry.grid(row=i*2+2, column=0, padx=10, pady=5, sticky="ew")
        entry.insert("1.0", db.get_value(key, ''))
        api_entries[key] = entry

    # Use Shodan Data Checkbox
    use_shodan_var = ctk.BooleanVar(value=db.get_value('USE_SHODAN_DATA', 'False') == 'True')
    use_shodan_checkbox = ctk.CTkCheckBox(api_frame, 
                                          font=("Arial", 11),  # Reduced font size
                                          text="Fetch Data From Shodan", 
                                          variable=use_shodan_var,
                                          width=20,  # Reduced width
                                          height=20,  # Reduced height
                                          checkbox_width=16,  # Reduced checkbox width
                                          checkbox_height=16)  # Reduced checkbox height
    use_shodan_checkbox.grid(row=len(api_fields)*2+1, column=0, padx=10, pady=5, sticky="w")  # Reduced padding

    def save_settings():
        global smtp_host_var, smtp_port_var
        # Save SMTP settings
        for key, entry in smtp_entries.items():
            db.set_value(key, entry.get())
        db.set_value('SMTP_SECURITY', smtp_security_var.get())

        # Save API credentials
        for key, entry in api_entries.items():
            db.set_value(key, entry.get("1.0", "end-1c").strip())  # Use strip() to remove any whitespace
        db.set_value('USE_SHODAN_DATA', str(use_shodan_var.get()))

        # Update main window SMTP fields
        smtp_host_var.set(smtp_entries['SMTP_HOST'].get())
        smtp_port_var.set(smtp_entries['SMTP_PORT'].get())

        messagebox.showinfo("Settings Saved", "Your settings have been saved successfully.")
        settings_window.grab_release()  # Release the grab before destroying
        settings_window.destroy()

    def cancel_settings():
        settings_window.grab_release()  # Release the grab before destroying
        settings_window.destroy()

    # Apply and Cancel buttons
    button_frame = ctk.CTkFrame(settings_window)
    button_frame.grid(row=1, column=0, columnspan=2, pady=20, sticky="ew")
    apply_button = ctk.CTkButton(button_frame, text="Apply", command=save_settings)
    apply_button.pack(side="left", padx=10, expand=True, fill="x")
    cancel_button = ctk.CTkButton(button_frame, text="Cancel", command=cancel_settings)
    cancel_button.pack(side="right", padx=10, expand=True, fill="x")

    # Configure grid weights for resizing
    settings_window.grid_columnconfigure(0, weight=1)
    settings_window.grid_columnconfigure(1, weight=1)
    settings_window.grid_rowconfigure(0, weight=1)
    smtp_frame.grid_columnconfigure(1, weight=1)
    api_frame.grid_columnconfigure(0, weight=1)

def get_host_and_port():
    global server_process, root, smtp_host_var, smtp_port_var
    env_host = db.get_value('LAN_IP', '127.0.0.1')
    env_port = db.get_value('PORT', '8000')
    env_smtp_host = db.get_value('SMTP_HOST', 'localhost')
    env_smtp_port = db.get_value('SMTP_PORT', '25')
    server_status = db.get_value('SERVER_STATUS', 'stopped')
    server_pid = db.get_value('SERVER_PID', '')
    backed = False
    
    print(server_status)
    print(env_host)
    print(env_port)
    print(server_pid)
    print(server_pid != '' and psutil.pid_exists(int(server_pid)) is not None)
    
    
    if(server_pid != '' and psutil.pid_exists(int(server_pid)) is not None):
        backed = True

    ctk.set_appearance_mode("Dark")  # Options: "Dark", "Light"
    ctk.set_default_color_theme("blue")  # Optional theme settings

    root = ctk.CTk()  # Use customTkinter's CTk
    root.title("Attacking Server")
    root.geometry("370x370")
    root.resizable(True, True) 

    lan_ip = get_lan_ip()

    host_var = ctk.StringVar(value=env_host)
    port_var = ctk.StringVar(value=env_port)
    smtp_host_var = ctk.StringVar(value=env_smtp_host)
    smtp_port_var = ctk.StringVar(value=env_smtp_port)

    # Create a grid layout for host and port in one row
    row_frame = ctk.CTkFrame(root)
    row_frame.grid(row=0, column=0, padx=10, pady=5, columnspan=2, sticky="nsew")
    
    # Select host column (left side)
    ctk.CTkLabel(row_frame, text="Select Host:", font=("Arial", 12)).grid(row=0, column=0, sticky="w", padx=10, pady=10)
    localhost_btn = ctk.CTkRadioButton(row_frame, text="Localhost (127.0.0.1)", font=("Arial", 12), variable=host_var, value="127.0.0.1")
    lan_ip_btn = ctk.CTkRadioButton(row_frame, text=f"LAN IP ({lan_ip})", variable=host_var, value=lan_ip)
    ngrok_btn = ctk.CTkRadioButton(row_frame, text="ngrok (Public URL)", variable=host_var, value="ngrok")
    localhost_btn.grid(row=1, column=0, sticky="w", padx=10)
    lan_ip_btn.grid(row=2, column=0, sticky="w", padx=10)
    ngrok_btn.grid(row=3, column=0, sticky="w", padx=10, pady=10)

    # Enter port column (middle)
    ctk.CTkLabel(row_frame, text="Enter Port:", font=("Arial", 12)).grid(row=0, column=1, sticky="w", padx=10)
    port_entry = ctk.CTkEntry(row_frame, textvariable=port_var)
    port_entry.grid(row=1, column=1, padx=10, pady=10)

    # SMTP settings
    smtp_frame = ctk.CTkFrame(root)
    smtp_frame.grid(row=1, column=0, padx=10, pady=5, columnspan=2, sticky="nsew")
    
    ctk.CTkLabel(smtp_frame, text="SMTP Host:", font=("Arial", 12)).grid(row=0, column=0, sticky="w", padx=10, pady=5)
    smtp_host_entry = ctk.CTkEntry(smtp_frame, textvariable=smtp_host_var, state="disabled")
    smtp_host_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

    ctk.CTkLabel(smtp_frame, text="SMTP Port:", font=("Arial", 12)).grid(row=1, column=0, sticky="w", padx=10, pady=5)
    smtp_port_entry = ctk.CTkEntry(smtp_frame, textvariable=smtp_port_var, state="disabled")
    smtp_port_entry.grid(row=1, column=1, padx=10, sticky="ew")

    # Settings button as plain text, floating right
    settings_button = ctk.CTkLabel(smtp_frame, text="Settings", font=("Arial", 12), cursor="hand2")
    settings_button.grid(row=2, column=1, padx=10, sticky="e")
    settings_button.bind("<Button-1>", lambda e: open_settings_window())

    # Configure column weights to make input boxes expand
    smtp_frame.columnconfigure(1, weight=1)

    # Row for loader (left) and buttons (right)
    button_frame = ctk.CTkFrame(root)
    button_frame.grid(row=2, column=0, padx=10, pady=5, columnspan=2, sticky="nsew")
    # Buttons (floating right)
    start_button = ctk.CTkButton(button_frame, text="Start Server", fg_color="#4CAF50", text_color="white", corner_radius=10, height=40)
    open_button = ctk.CTkButton(button_frame, text="Open Interface", state=ctk.DISABLED, fg_color="#2196F3", text_color="white", corner_radius=10, height=40)
    close_button = ctk.CTkButton(button_frame, text="Close Server", state=ctk.DISABLED, fg_color="#F44336", text_color="white", corner_radius=10, height=40)
    filling_button = ctk.CTkButton(button_frame, text="", state=ctk.DISABLED, fg_color=button_frame.cget("fg_color"), corner_radius=10, height=40)
    # Place buttons in a grid
    

    def on_submit():
        host = host_var.get()
        port = port_var.get()
        smtp_host = smtp_host_var.get()
        smtp_port = smtp_port_var.get()

        if not port.isdigit() or not (1 <= int(port) <= 65535):
            ctk.messagebox.showerror("Invalid Input", "Please enter a valid port number (1-65535).")
        elif not smtp_port.isdigit() or not (1 <= int(smtp_port) <= 65535):
            ctk.messagebox.showerror("Invalid Input", "Please enter a valid SMTP port number (1-65535).")
        else:
            start_button.configure(state=ctk.DISABLED)
            threading.Thread(target=start_django, args=(host, port, start_button, filling_button, open_button, close_button, port_entry, [localhost_btn, lan_ip_btn, ngrok_btn], smtp_host_entry, smtp_port_entry)).start()

    start_button.configure(command=on_submit)
    filling_button.configure(state=ctk.DISABLED)
    open_button.configure(command=lambda: webbrowser.open(f"http://{host_var.get()}:{port_var.get()}"))
    close_button.configure(command=lambda: stop_django(host_var.get(), port_var.get(), start_button, filling_button, open_button, close_button, port_entry, [localhost_btn, lan_ip_btn, ngrok_btn], smtp_host_entry, smtp_port_entry))

    root.grid_columnconfigure(0, weight=1)
    root.grid_columnconfigure(1, weight=1)
    root.grid_rowconfigure(0, weight=1)
    root.grid_rowconfigure(1, weight=1)
    button_frame.grid_columnconfigure(0, weight=1)
    button_frame.grid_columnconfigure(1, weight=1)
    
    try:
        if (server_status == 'running' and backed ) or backed:
            server_process = psutil.Process(int(server_pid))
            host_var.set(env_host)
            port_var.set(env_port)
            start_button.grid_forget()
            filling_button.grid_forget()
            open_button.configure(state=ctk.NORMAL)
            open_button.grid(row=2, column=0,  sticky="ew", padx=10, columnspan=1, pady=10)
            close_button.configure(state=ctk.NORMAL)
            close_button.grid(row=2, column=1, columnspan=1, padx=10, pady=10, sticky="ew")
            port_entry.configure(state=ctk.DISABLED)
            localhost_btn.configure(state=ctk.DISABLED)
            lan_ip_btn.configure(state=ctk.DISABLED)
        else:
            start_button.grid(row=2, column=1,  sticky="ew", padx=10, columnspan=1, pady=10)
            filling_button.grid(row=2, column=0,  sticky="ew", padx=10, columnspan=1, pady=10)
            open_button.grid_forget()
            close_button.grid_forget()
            port_entry.configure(state=ctk.NORMAL)
            localhost_btn.configure(state=ctk.NORMAL)
            lan_ip_btn.configure(state=ctk.NORMAL)
    except Exception as e:
        root.withdraw()
        show_error_window(str(e))

   
    root.mainloop()

def reset_ui_state(start_button, port_entry, host_buttons):
    start_button.configure(state=ctk.NORMAL)
    port_entry.configure(state=ctk.NORMAL)
    for btn in host_buttons:
        btn.configure(state=ctk.NORMAL)

if __name__ == "__main__":
    get_host_and_port()

atexit.register(db.close)