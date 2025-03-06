import tkinter as tk
from tkinter import ttk
from tkcalendar import DateEntry
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from calculate_monthly_rev_plot import calculate_revenue, plot_revenue_comparison
from datetime import datetime
from matplotlib.ticker import FuncFormatter

class ScrollableFrame(ttk.Frame):
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        
        # Create a canvas and scrollbar
        self.canvas = tk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        
        # Create the scrollable frame
        self.scrollable_frame = ttk.Frame(self.canvas)
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        # Add the frame to the canvas
        self.canvas_frame = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        # Configure the canvas
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        # Grid layout
        self.canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        # Configure grid weights
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Bind canvas resizing
        self.canvas.bind('<Configure>', self.on_canvas_configure)
        
        # Bind all types of scrolling
        self.bind_scroll_events()
    
    def on_canvas_configure(self, event):
        # Update the width of the frame to fill the canvas
        self.canvas.itemconfig(self.canvas_frame, width=event.width)
    
    def on_scroll(self, event):
        # Handle different types of scroll events
        if event.num == 5 or event.delta < 0:  # Scroll down
            self.canvas.yview_scroll(1, "units")
        elif event.num == 4 or event.delta > 0:  # Scroll up
            self.canvas.yview_scroll(-1, "units")
    
    def on_trackpad_scroll(self, event):
        # Handle trackpad scrolling (macOS)
        if event.delta:
            # Convert trackpad scroll to canvas movement
            self.canvas.yview_scroll(int(-1 * event.delta), "units")
    
    def bind_scroll_events(self):
        # Bind mouse wheel on Windows and Linux
        self.canvas.bind_all("<MouseWheel>", self.on_scroll)
        
        # Bind mouse wheel for Linux
        self.canvas.bind_all("<Button-4>", self.on_scroll)
        self.canvas.bind_all("<Button-5>", self.on_scroll)
        
        # Bind trackpad scrolling for macOS
        self.canvas.bind_all("<MouseWheel>", self.on_trackpad_scroll)
        self.canvas.bind_all("<Shift-MouseWheel>", self.on_trackpad_scroll)
        self.canvas.bind_all("<Control-MouseWheel>", self.on_trackpad_scroll)

class MiningCalculatorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Bitcoin Mining Revenue Calculator")
        self.root.geometry("800x600")  # Changed initial size
        
        # Configure root grid weights
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        
        # Create scrollable frame
        self.scroll_frame = ScrollableFrame(root)
        self.scroll_frame.grid(row=0, column=0, sticky="nsew")
        
        # Create main frame with padding inside scrollable frame
        main_frame = ttk.Frame(self.scroll_frame.scrollable_frame, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Mining Power Input
        input_frame = ttk.Frame(main_frame)
        input_frame.grid(row=0, column=0, sticky="ew", pady=5)
        input_frame.grid_columnconfigure(1, weight=1)
        
        ttk.Label(input_frame, text="Mining Power (TH/s):").grid(row=0, column=0, sticky="w", padx=(0,10))
        self.mining_power = ttk.Entry(input_frame)
        self.mining_power.grid(row=0, column=1, sticky="ew")
        
        # Start Date Input
        date_frame = ttk.Frame(main_frame)
        date_frame.grid(row=1, column=0, sticky="ew", pady=5)
        date_frame.grid_columnconfigure(1, weight=1)
        
        ttk.Label(date_frame, text="Start Date:").grid(row=0, column=0, sticky="w", padx=(0,10))
        self.start_date = DateEntry(date_frame, width=20, background='darkblue',
                                  foreground='white', borderwidth=2)
        self.start_date.grid(row=0, column=1, sticky="w")
        
        # Month Selection Frame
        month_frame = ttk.LabelFrame(main_frame, text="Select Months", padding="10")
        month_frame.grid(row=2, column=0, sticky="ew", pady=10)
        month_frame.grid_columnconfigure((0,1,2,3), weight=1)
        
        # Month Toggle Buttons
        self.months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                      "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        self.month_vars = {}
        
        for i, month in enumerate(self.months):
            row = i // 4
            col = i % 4
            self.month_vars[month] = tk.BooleanVar(value=True)
            ttk.Checkbutton(month_frame, text=month, 
                           variable=self.month_vars[month]).grid(row=row, column=col, padx=5, pady=5)
        
        # Calculate Button
        ttk.Button(main_frame, text="Calculate Revenue", 
                  command=self.calculate).grid(row=3, column=0, pady=10, sticky="ew")
        
        # Frame for plot
        self.plot_frame = ttk.Frame(main_frame)
        self.plot_frame.grid(row=4, column=0, sticky="nsew")
        self.plot_frame.grid_columnconfigure(0, weight=1)
        
        # Results Text
        self.results_text = tk.Text(main_frame, height=4, wrap=tk.WORD)
        self.results_text.grid(row=5, column=0, sticky="ew", pady=10)
    
    def calculate(self):
        try:
            # Clear previous results
            self.results_text.delete(1.0, tk.END)
            for widget in self.plot_frame.winfo_children():
                widget.destroy()
            
            # Get input values
            mining_power = float(self.mining_power.get())
            start_date = self.start_date.get_date().strftime("%Y-%m-%d")
            selected_months = [month for month, var in self.month_vars.items() if var.get()]
            
            if not selected_months:
                self.results_text.insert(tk.END, "Please select at least one month.")
                return
            
            # Calculate revenue
            dates, fiat_revenue, satoshi_revenue, total_fiat, total_sats, total_sats_fiat_value, bitcoin_price = \
                calculate_revenue(mining_power, start_date, selected_months)
            
            # Create figure and embed in GUI
            fig = plt.Figure(figsize=(10, 5), dpi=100)
            fig.set_tight_layout(True)  # Adjust layout to prevent label cutoff
            ax1 = fig.add_subplot(111)
            
            # Set the left Y-axis range to the larger of total fiat revenue or total sats fiat value
            max_y_value = max(total_fiat, total_sats_fiat_value)
            ax1.set_ylim(0, max_y_value * 1.1)  # Scale up by 10% to add margin
            
            # Plot data
            ax1.set_xlabel("Date")
            ax1.set_ylabel("Fiat Revenue ($)", color="blue")
            line1 = ax1.plot(dates, fiat_revenue, label="Fiat Revenue ($)", color="blue")[0]
            ax1.tick_params(axis='y', labelcolor="blue")
            
            # Right Y-axis (Total Satoshis Mined, NOT Scaled to Fiat)
            ax2 = ax1.twinx()
            ax2.set_ylabel("Total Satoshis Mined", color="orange")
            ax2.set_ylim(0, total_sats * 1.1)  # Scale up by 10% to prevent cutoff
            line2 = ax2.plot(dates, satoshi_revenue, label="Satoshi Revenue", color="orange")[0]
            ax2.tick_params(axis='y', labelcolor="orange")
            
            # Format the right Y-axis for satoshi readability
            ax2.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{int(x):,} sats"))
            
            # Add legend
            lines = [line1, line2]
            labels = [line.get_label() for line in lines]
            ax1.legend(lines, labels, loc='upper left')
            
            # Rotate x-axis labels for better readability
            plt.setp(ax1.get_xticklabels(), rotation=45, ha='right')
            
            # Update the title with the total satoshis mined
            ax1.set_title(
                f"Fiat vs. Satoshi Revenue Over Time\n"
                f"Fiat Savings (Sold Weekly): ${total_fiat:.2f} | "
                f"Total Satoshis Mined: {round(total_sats):,} sats | "
                f"Satoshi Value (Held): ${total_sats_fiat_value:.2f} at ${bitcoin_price:.2f}/BTC"
            )
            
            # Add the plot to the GUI
            canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
            canvas.draw()
            canvas_widget = canvas.get_tk_widget()
            canvas_widget.grid(row=0, column=0, sticky="nsew")
            
            # Make the plot responsive
            self.plot_frame.grid_columnconfigure(0, weight=1)
            self.plot_frame.grid_rowconfigure(0, weight=1)
            
            # Display results
            results = (f"Total Fiat Revenue (Selling Weekly): ${total_fiat:.2f}\n"
                      f"Total Satoshis Mined (Held): {total_sats:,} sats\n"
                      f"Satoshi Value (Held): ${total_sats_fiat_value:.2f} at ${bitcoin_price:.2f}/BTC")
            self.results_text.insert(tk.END, results)
            
        except ValueError as e:
            self.results_text.insert(tk.END, f"Error: Please check your inputs. {str(e)}")
        except Exception as e:
            self.results_text.insert(tk.END, f"Error: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = MiningCalculatorGUI(root)
    root.mainloop()