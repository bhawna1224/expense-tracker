import sqlite3
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import simpledialog, messagebox
from datetime import datetime

# Step 1: Set up SQLite database
conn = sqlite3.connect('budget.db')
c = conn.cursor()

# Create expenses table with the new "investment" column
c.execute('''CREATE TABLE IF NOT EXISTS expenses
             (id INTEGER PRIMARY KEY AUTOINCREMENT, category TEXT, month TEXT, date DATE, description TEXT, amount REAL)''')

# Create budget allocation table
c.execute('''CREATE TABLE IF NOT EXISTS budget_allocation
             (id INTEGER PRIMARY KEY AUTOINCREMENT, category TEXT, month TEXT, amount REAL)''')

# Global variable to store monthly salary
monthly_salary = 0.0

# Step 2: Function to get budget allocation for a category in a specific month
def get_budget_allocation(category, month):
    c.execute("SELECT amount FROM budget_allocation WHERE category=? AND month=?", (category, month))
    row = c.fetchone()
    if row:
        return row[0]
    else:
        return 0.0

# Step 3: Function to add expense to the database
def add_expense(category, month, date, description, amount ):
    # Add expense to the database for the selected month
    c.execute("INSERT INTO expenses (category, month, date, description, amount) VALUES (?, ?, ?, ?, ?)",
              (category, month, date, description, amount))
    conn.commit()

# Step 4: Function to generate graphs/charts for a given month
def generate_graphs(month):
    # Create a single figure to hold all the subplots
    fig, axes = plt.subplots(3, 1, figsize=(10, 18), gridspec_kw={'height_ratios': [3, 2, 2]})

    # Get total expenses for each category in the given month
    c.execute("SELECT category, SUM(amount) FROM expenses WHERE month=? GROUP BY category", (month,))
    expenses_data = c.fetchall()
    categories = [row[0] for row in expenses_data]
    expenses = [row[1] for row in expenses_data]

    # Plot pie chart for expenses
    axes[0].pie(expenses, labels=categories, autopct='%1.1f%%')
    axes[0].set_title('Monthly Expenses Breakdown for {}'.format(month))

    c.execute("SELECT DISTINCT category FROM budget_allocation")
    categories_data = c.fetchall()
    categories = [row[0] for row in categories_data]
    # Get budget allocation for each category in the given month
    budget_allocation = {category: get_budget_allocation(category, month) for category in categories}
    # Calculate remaining savings
    total_expenses = sum(expenses)
    savings = monthly_salary - total_expenses

    # Plot bar chart for budget allocation and savings
    axes[1].bar(budget_allocation.keys(), [budget_allocation[category] for category in budget_allocation], label='Budget Allocation')
    axes[1].bar(['Savings'], [savings], label='Savings')
    axes[1].set_xlabel('Categories')
    axes[1].set_ylabel('Amount')
    axes[1].set_title('Budget Allocation vs Savings for {}'.format(month))
    axes[1].legend()

    # Get distinct months from the expenses table
    c.execute("SELECT DISTINCT month FROM expenses")
    months_data = c.fetchall()
    months = [row[0] for row in months_data]

    total_expenses = []
    total_savings = []
    for month in months:
        # Get total expenses for the month
        c.execute("SELECT SUM(amount) FROM expenses WHERE month=?", (month,))
        total_expense = c.fetchone()[0] or 0  # If there are no expenses, default to 0
        total_expenses.append(total_expense)

        # Get budget allocation for the month
        c.execute("SELECT SUM(amount) FROM budget_allocation WHERE month=?", (month,))
        total_budget = c.fetchone()[0] or 0  # If there are no budget allocations, default to 0
        savings = monthly_salary - total_expense
        total_savings.append(savings)

    # Plotting
    index = range(len(months))
    axes[2].bar(index, total_expenses, 0.35, label='Total Expenses')
    axes[2].bar([i + 0.35 for i in index], total_savings, 0.35, label='Total Savings')
    axes[2].set_xlabel('Months')
    axes[2].set_ylabel('Amount')
    axes[2].set_title('Total Expenses and Savings for Each Month')
    axes[2].set_xticks([i + 0.35 / 2 for i in index])
    axes[2].set_xticklabels(months)
    axes[2].legend()

    # Adjust layout and add gaps between subplots
    plt.tight_layout(pad=7.0)

    # Show the plot
    plt.show()

# Step 5: Define Tkinter GUI
class BudgetApp:
    def __init__(self, master):
        self.master = master
        master.title("Budget Management")

        # Labels and Entry widgets for monthly salary
        self.salary_label = tk.Label(master, text="Enter your monthly salary:")
        self.salary_label.grid(row=0, column=0, sticky="w")
        self.salary_entry = tk.Entry(master)
        self.salary_entry.grid(row=0, column=1)

        # Button to submit salary
        self.salary_button = tk.Button(master, text="Submit", command=self.submit_salary)
        self.salary_button.grid(row=0, column=2)

        # Dropdown menu for selecting month
        self.month_label = tk.Label(master, text="Select month:")
        self.month_label.grid(row=1, column=0, sticky="w")
        self.month_var = tk.StringVar(master)
        self.month_dropdown = tk.OptionMenu(master, self.month_var, *self.get_months())
        self.month_dropdown.grid(row=1, column=1, columnspan=2)

        # Button to add new month
        self.add_month_button = tk.Button(master, text="Add New Month", command=self.add_new_month)
        self.add_month_button.grid(row=2, column=0, columnspan=3)

        # Button to add allocation
        self.add_allocation_button = tk.Button(master, text="Add Allocation", command=self.add_allocation)
        self.add_allocation_button.grid(row=3, column=0, columnspan=3)

        # Budget allocation frame
        self.budget_frame = tk.Frame(master)
        self.budget_frame.grid(row=4, column=0, columnspan=3)

        # Expenses frame
        self.expenses_frame = tk.Frame(master)
        self.expenses_frame.grid(row=5, column=0, columnspan=3)

        # Button to add expense
        self.add_expense_button = tk.Button(master, text="Add Expense", command=self.add_expense_popup)
        self.add_expense_button.grid(row=6, column=0, columnspan=3)

        # Button to view expenses
        self.view_expense_button = tk.Button(master, text="View Expenses", command=self.view_expenses)
        self.view_expense_button.grid(row=7, column=0, columnspan=3)

        # Button to generate graphs
        self.graph_button = tk.Button(master, text="Generate Graphs", command=self.generate_graphs)
        self.graph_button.grid(row=8, column=0, columnspan=3)

    def submit_salary(self):
        global monthly_salary
        try:
            monthly_salary = float(self.salary_entry.get())
            self.create_budget_allocation_widgets()
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid salary.")

    def get_months(self):
        c.execute("SELECT DISTINCT month FROM budget_allocation")
        months = [row[0] for row in c.fetchall()]
        if not months:
            months = ["No months available"]
        return months

    def create_budget_allocation_widgets(self):
        selected_month = self.month_var.get()
        if not selected_month:
            messagebox.showerror("Error", "Please select a month.")
            return

        # Check if a budget allocation for the selected month already exists
        c.execute("SELECT * FROM budget_allocation WHERE month=?", (selected_month,))
        existing_allocation = c.fetchone()
        if existing_allocation:
            messagebox.showerror("Error", "Budget allocation for this month already exists.")
            return

        categories = ['housing', 'transportation', 'food', 'utilities', 'entertainment', 'savings','investment']
        for i, category in enumerate(categories):
            label = tk.Label(self.budget_frame, text=f"Enter budget allocation for {category}:")
            label.grid(row=i, column=0, sticky="w")
            entry = tk.Entry(self.budget_frame)
            entry.grid(row=i, column=1)
            setattr(self, f"{category}_entry", entry)

    def add_new_month(self):
        try:
            new_month = simpledialog.askstring("Input", "Enter the new month (YYYY-MM):", parent=self.master)
            if new_month:
                # Validate the format of the new month
                datetime.strptime(new_month, '%Y-%m')
                c.execute("SELECT DISTINCT month FROM budget_allocation WHERE month=?", (new_month,))
                existing_month = c.fetchone()
                if existing_month:
                    messagebox.showerror("Error", "Budget allocation for this month already exists.")
                else:
                    self.month_dropdown['menu'].add_command(label=new_month, command=tk._setit(self.month_var, new_month))
        except ValueError:
            messagebox.showerror("Error", "Please enter the new month in the format YYYY-MM.")

    def add_allocation(self):
        selected_month = self.month_var.get()
        if not selected_month:
            messagebox.showerror("Error", "Please select a month.")
            return

        # Check if a budget allocation for the selected month already exists
        c.execute("SELECT * FROM budget_allocation WHERE month=?", (selected_month,))
        existing_allocation = c.fetchone()
        if existing_allocation:
            messagebox.showerror("Error", "Budget allocation for this month already exists.")
            return

        categories = ['housing', 'transportation', 'food', 'utilities', 'entertainment', 'savings','investment']
        for category in categories:
            amount_entry = getattr(self, f"{category}_entry")
            amount = amount_entry.get()
            try:
                amount = float(amount)
                c.execute("INSERT INTO budget_allocation (category, month, amount) VALUES (?, ?, ?)",
                          (category, selected_month, (amount*monthly_salary)/100))
                conn.commit()
            except ValueError:
                messagebox.showerror("Error", f"Please enter a valid amount for {category}.")

        messagebox.showinfo("Success", "Budget allocation added successfully.")

    def add_expense_popup(self):
        popup = tk.Toplevel(self.master)
        popup.title("Add Expense")

        # Labels and Entry widgets for expense details
        tk.Label(popup, text="Category:").grid(row=0, column=0, sticky="w")
        self.category_entry_popup = tk.Entry(popup)
        self.category_entry_popup.grid(row=0, column=1)

        tk.Label(popup, text="Date (YYYY-MM-DD):").grid(row=1, column=0, sticky="w")
        self.date_entry_popup = tk.Entry(popup)
        self.date_entry_popup.grid(row=1, column=1)

        tk.Label(popup, text="Description:").grid(row=2, column=0, sticky="w")
        self.description_entry_popup = tk.Entry(popup)
        self.description_entry_popup.grid(row=2, column=1)

        tk.Label(popup, text="Amount:").grid(row=3, column=0, sticky="w")
        self.amount_entry_popup = tk.Entry(popup)
        self.amount_entry_popup.grid(row=3, column=1)

        # Button to submit expense
        tk.Button(popup, text="Submit", command=self.add_expense).grid(row=5, column=0, columnspan=2)

    def add_expense(self):
        try:
            category = self.category_entry_popup.get()
            date = self.date_entry_popup.get()
            description = self.description_entry_popup.get()
            amount = float(self.amount_entry_popup.get())
            selected_month = self.month_var.get()

            # Ensure expense is added only for the selected month
            if date.startswith(selected_month):
                add_expense(category, selected_month, date, description, amount)
                messagebox.showinfo("Success", "Expense added successfully.")
            else:
                messagebox.showerror("Error", "Expense date does not match selected month.")
        except ValueError:
            messagebox.showerror("Error", "Please enter valid amounts.")

    def view_expenses(self):
        selected_month = self.month_var.get()
        if not selected_month:
            messagebox.showerror("Error", "Please select a month.")
            return

        # Fetch all expenses for the selected month
        c.execute("SELECT * FROM expenses WHERE month=?", (selected_month,))
        expenses_data = c.fetchall()

        # Create a new window to display expenses
        expense_window = tk.Toplevel(self.master)
        expense_window.title("Expenses for {}".format(selected_month))

        # Display expenses in a list
        for i, expense in enumerate(expenses_data):
            tk.Label(expense_window, text=f"{expense[3]} - {expense[1]} - {expense[5]}").grid(row=i, column=0, sticky="w")

            # Add delete button for each expense
            tk.Button(expense_window, text="Delete", command=lambda x=expense[0]: self.delete_expense(x)).grid(row=i, column=1)

    def delete_expense(self, expense_id):
        try:
            c.execute("DELETE FROM expenses WHERE id=?", (expense_id,))
            conn.commit()
            messagebox.showinfo("Success", "Expense deleted successfully.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def generate_graphs(self):
        try:
            selected_month = self.month_var.get()
            if not selected_month:
                messagebox.showerror("Error", "Please select a month.")
                return
            generate_graphs(selected_month)
        except Exception as e:
            messagebox.showerror("Error", str(e))

def main():
    root = tk.Tk()
    app = BudgetApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()

# Close database connection
conn.close()
