import tkinter as tk
from tkinter import ttk, messagebox
import requests
from threading import Thread, Event
from queue import Queue
import tkinter.filedialog


class BdixTesterApp:
    TIMEOUT = 1
    PROGRESS_LENGTH = 300
    SERVERS_URL = "https://gist.githubusercontent.com/Tazhossain/e0aecd399c1fb18d1094ebae1f735f0e/raw/Bdix.txt"
    WINDOW_WIDTH = 350
    WINDOW_HEIGHT = 400

    def __init__(self, root):
        self.root = root
        self.root.title("Bdix Tester Tool")
        self.root.geometry(f"{self.WINDOW_WIDTH}x{self.WINDOW_HEIGHT}")
        self.root.configure(bg="#2C3E50")

        self.category_var = tk.StringVar(value="FTP")
        self.working_servers_queue = Queue()
        self.testing_flag = True
        self.testing_complete_event = Event()

        self.create_gui()

    def create_gui(self):
        # Header
        self.create_label("Bdix Tester Tool", 18)

        # Category selection
        self.create_category_selection()

        # Start Button
        self.start_button = self.create_button("Start", self.start_testing, "#16A085")

        # Stop Button
        self.create_button("Stop", self.stop_testing, "#C0392B")

        # Working Progress
        self.create_label("Testing:", 14)
        self.create_progressbar()

        # Working Servers Count
        self.working_count_var = tk.StringVar(value="0")
        self.create_label("Found:", 14)
        self.create_label_display(self.working_count_var)

        # Display Working Servers
        self.save_button = self.create_button("Save", self.save_working_servers, "#2ECC71")
        self.save_button.configure(font=("Helvetica", 12))
        self.save_button.pack(side=tk.RIGHT)
        self.save_button.place(x=300, y=367)
        self.display_button = self.create_button("Servers", self.display_working_servers, "#3498DB")
        self.display_button.configure(font=("Helvetica", 12))
        self.display_button.place(x=141, y=318)

        # Mini "Made by Taz" credit
        taz_label = tk.Label(self.root, text="Taz", font=("Helvetica", 10, "italic", "bold"), bg="#2C3E50", fg="#E74C3C")
        taz_label.pack(side=tk.RIGHT, pady=5)
        taz_label.place(x=10, y=370)

    def create_category_selection(self):
        frame = tk.Frame(self.root, bg="#2C3E50")
        frame.pack(side=tk.TOP, pady=10)

        ftp_checkbox = ttk.Checkbutton(frame, text="FTP", variable=self.category_var, onvalue="FTP",
                                       offvalue="", state=tk.NORMAL)
        ftp_checkbox.pack(side=tk.LEFT, padx=10)

        tv_checkbox = ttk.Checkbutton(frame, text="TV", variable=self.category_var, onvalue="TV",
                                      offvalue="", state=tk.NORMAL)
        tv_checkbox.pack(side=tk.LEFT, padx=10)

    def create_label(self, text, font_size):
        label = tk.Label(self.root, text=text, font=("Helvetica", font_size), bg="#2C3E50", fg="white")
        label.pack(pady=5)

    def create_button(self, text, command, bg_color, state=tk.NORMAL):
        button = tk.Button(self.root, text=text, command=command, bg=bg_color, fg="white",
                           font=("Helvetica", 14), state=state)
        button.pack(pady=5)
        return button

    def create_progressbar(self):
        self.working_progress = ttk.Progressbar(self.root, orient="horizontal", length=self.PROGRESS_LENGTH,
                                               mode="determinate", style="TProgressbar")
        self.working_progress.pack()

    def create_label_display(self, text_variable):
        label_display = tk.Label(self.root, textvariable=text_variable, font=("Helvetica", 14), bg="#2C3E50",
                                 fg="white")
        label_display.pack()

    def disable_category_checkboxes(self):
        for child in self.root.winfo_children():
            if isinstance(child, tk.Frame):
                for checkbox in child.winfo_children():
                    checkbox.configure(state=tk.DISABLED)

    def enable_category_checkboxes(self):
        for child in self.root.winfo_children():
            if isinstance(child, tk.Frame):
                for checkbox in child.winfo_children():
                    checkbox.configure(state=tk.NORMAL)

    def reset_progress_bar(self):
        self.working_progress.configure(style="TProgressbar")
        self.working_progress["value"] = 0

    def check_completion(self):
        self.testing_complete_event.wait()
        self.update_progress_bar()

    def update_progress_bar(self):
        self.reset_progress_bar()
        self.testing_complete_event.clear()

    def start_testing(self):
        category = self.category_var.get()
        self.working_servers_queue.queue.clear()
        self.reset_progress_bar()
        self.testing_flag = True

        self.disable_category_checkboxes()
        self.start_button.configure(state=tk.DISABLED)

        Thread(target=self.test_servers, args=(category,), daemon=True).start()
        Thread(target=self.check_completion, daemon=True).start()

    def stop_testing(self):
        self.testing_flag = False
        self.enable_category_checkboxes()
        self.start_button.configure(state=tk.NORMAL)
        messagebox.showinfo("Bdix Tester Tool", "Testing Stopped!")

    def test_servers(self, category):
        servers = self.read_servers_from_file(category)
        total_servers = len(servers)

        for index, server in enumerate(servers, start=1):
            if not self.testing_flag:
                break

            if not server.startswith(("http://", "https://")):
                server = f"http://{server}"

            try:
                response = requests.get(server, timeout=self.TIMEOUT)
                if response.status_code == 200:
                    self.working_servers_queue.put(server)
                    self.working_count_var.set(self.working_servers_queue.qsize())
            except requests.RequestException:
                pass

            progress_value = int((index / total_servers) * 100)
            self.working_progress["value"] = progress_value
            self.root.update_idletasks()

        if self.testing_flag:
            messagebox.showinfo("Bdix Tester Tool", "Testing Completed!")

        self.testing_complete_event.set()

    def read_servers_from_file(self, category):
        try:
            response = requests.get(self.SERVERS_URL)
            response.raise_for_status()
            content = response.text

            start_marker = f"#{category.upper()}:"
            end_marker = f"#{category.upper()} CATEGORY ENDED#"
            start_index = content.find(start_marker)
            end_index = content.find(end_marker, start_index + 1) if start_index != -1 else -1

            if start_index != -1 and end_index != -1:
                servers = content[start_index + len(start_marker):end_index].strip().split("\n")
                return servers
            else:
                messagebox.showerror("Bdix Tester Tool", f"No servers found for the category: {category}")
                return []
        except requests.RequestException:
            messagebox.showerror("Bdix Tester Tool", "Failed to fetch server list from the URL.")
            return []

    def save_working_servers(self):
        if not self.working_servers_queue.queue:
            messagebox.showinfo("Bdix Tester Tool", "No working servers to save.")
            return

        try:
            default_filename = "server.txt"  # Set your default filename here
            file_path = tkinter.filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt")],
                initialfile=default_filename
            )

            if file_path:
                with open(file_path, "w") as file:
                    for server in self.working_servers_queue.queue:
                        file.write(server + "\n")

                messagebox.showinfo("Bdix Tester Tool", f"Working servers saved to {file_path}")
            else:
                messagebox.showinfo("Bdix Tester Tool", "Save operation canceled.")
        except Exception as e:
            messagebox.showerror("Bdix Tester Tool", f"Error saving working servers: {e}")

    def display_working_servers(self):
        if not self.working_servers_queue.queue:
            messagebox.showinfo("Bdix Tester Tool", "No working servers to display.")
            return

        working_servers_window = tk.Toplevel(self.root)
        working_servers_window.title("Working Servers")

        scrollbar = ttk.Scrollbar(working_servers_window, orient=tk.VERTICAL)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.working_servers_canvas = tk.Canvas(working_servers_window, yscrollcommand=scrollbar.set, width=200,
                                               height=395)
        self.working_servers_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        frame = tk.Frame(self.working_servers_canvas)
        self.working_servers_canvas.create_window((0, 0), window=frame, anchor=tk.NW)

        # Adjust font size and width of server buttons
        font_size = 8  # Set your desired font size
        button_width = 30  # Set your desired button width

        for server in self.working_servers_queue.queue:
            server_button = tk.Button(
                frame, text=server, command=lambda s=server: self.open_browser(s),
                anchor=tk.W, justify=tk.LEFT, bg="#2ECC71", fg="white", font=("Helvetica", font_size),
                width=button_width
            )
            server_button.pack(pady=2, fill=tk.X)

        # Center the "Display Working Servers" button within the frame
        frame.update_idletasks()
        for widget in frame.winfo_children():
            widget.pack_configure(side=tk.TOP, anchor=tk.W, pady=2, fill=tk.X)

        self.working_servers_canvas.config(scrollregion=self.working_servers_canvas.bbox("all"))

        def on_canvas_configure(event):
            self.working_servers_canvas.config(scrollregion=self.working_servers_canvas.bbox("all"))

        def _mouse_scroll(event):
            self.working_servers_canvas.yview_scroll(-1 * int(event.delta / 120), "units")

        self.working_servers_canvas.bind("<Configure>", on_canvas_configure)
        self.working_servers_canvas.bind("<MouseWheel>", _mouse_scroll)
        self.working_servers_canvas.bind("<Button-4>", _mouse_scroll)
        self.working_servers_canvas.bind("<Button-5>", _mouse_scroll)

        scrollbar.config(command=self.working_servers_canvas.yview)

        # Position the working servers window beside the main window
        x = self.root.winfo_x() + self.root.winfo_width()
        y = self.root.winfo_y()
        working_servers_window.geometry(f"+{x}+{y}")

    def on_mouse_scroll(self, event):
        self.working_servers_canvas.yview_scroll(-1 * int(event.delta / 120), "units")

    def open_browser(self, url):
        import webbrowser
        webbrowser.open(url)


# Main
if __name__ == "__main__":
    root = tk.Tk()
    bdix_tester = BdixTesterApp(root)

    # Center the main window
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x_position = (screen_width - BdixTesterApp.WINDOW_WIDTH) // 2
    y_position = (screen_height - BdixTesterApp.WINDOW_HEIGHT) // 2

    root.geometry(f"{BdixTesterApp.WINDOW_WIDTH}x{BdixTesterApp.WINDOW_HEIGHT}+{x_position}+{y_position}")
    root.mainloop()