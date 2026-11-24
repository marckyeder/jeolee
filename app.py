import ctypes
import json
import os
import tkinter as tk
from tkinter import messagebox
from datetime import datetime


# ============================================
# HIGH-DPI DISPLAY FIX (CRISP VECTOR FONTS)
# ============================================
def enable_high_dpi():
    """Prevents OS bitmap stretching so Tkinter fonts render razor-sharp."""
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # Per-Monitor DPI Aware
    except Exception:
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass


enable_high_dpi()

DATA_FILE = "budget_data.json"

CATEGORIES = (
    "Food & Meals",
    "Commute & Fare",
    "School & Printing",
    "Load & Internet",
    "Personal & Misc"
)

CATEGORY_COLORS = {
    "Food & Meals": "#2563EB",
    "Commute & Fare": "#0D9488",
    "School & Printing": "#7C3AED",
    "Load & Internet": "#EA580C",
    "Personal & Misc": "#64748B"
}

QUICK_PRESETS = (
    ("Jeepney / Trike", "Commute & Fare"),
    ("Student Meal", "Food & Meals"),
    ("Print / Photocopy", "School & Printing"),
    ("Mobile Data Load", "Load & Internet")
)


class BudgetBalanceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Budget Balance — Mobile Allowance System")
        self.root.configure(bg="#EEF2F6")

        # Launch in Full Screen with F11 / Esc support
        self.is_fullscreen = True
        self.root.attributes("-fullscreen", True)
        self.root.bind("<F11>", self.toggle_fullscreen)
        self.root.bind("<Escape>", self.exit_fullscreen)

        self.data = self.load_data()
        self.active_tab = None
        self.current_pct_left = 0.0
        self.current_bar_color = "#22C55E"

        self.build_ui()
        self.log_process("SYSTEM", "Application initialized in High-DPI Full-Screen mode.")
        self.refresh_dashboard()

        if not self.data["is_configured"]:
            self.switch_tab("setup")
            self.log_process("WORKFLOW", "Configure allowance & fixed deductions.")
        else:
            self.switch_tab("log")
            self.log_process("WORKFLOW", "Active cycle detected. Ready to log expenses.")

    def toggle_fullscreen(self, event=None):
        self.is_fullscreen = not self.is_fullscreen
        self.root.attributes("-fullscreen", self.is_fullscreen)
        if not self.is_fullscreen:
            self.root.geometry("1100x760")
        self.screen_btn.config(
            text="Exit Fullscreen [Esc]" if self.is_fullscreen else "Fullscreen [F11]"
        )

    def exit_fullscreen(self, event=None):
        if self.is_fullscreen:
            self.is_fullscreen = False
            self.root.attributes("-fullscreen", False)
            self.root.geometry("1100x760")
            self.screen_btn.config(text="Fullscreen [F11]")

    # ============================================
    # MODULE 1: FILE STORAGE (PERSISTENCE)
    # ============================================
    def load_data(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as file:
                    return json.load(file)
            except (json.JSONDecodeError, IOError):
                pass
        return {
            "is_configured": False,
            "total_allowance": 0.0,
            "fixed_deductions": 0.0,
            "net_spendable": 0.0,
            "total_days": 0,
            "start_date": "",
            "expenses": []
        }

    def save_data(self):
        with open(DATA_FILE, "w", encoding="utf-8") as file:
            json.dump(self.data, file, indent=4)
        self.save_badge.config(text="● Saved to JSON", fg="#4ADE80")

    # ============================================
    # MODULE 4: SMART BALANCE & ALERT ENGINE
    # ============================================
    def get_budget_metrics(self):
        total_spent = round(sum(item["amount"] for item in self.data["expenses"]), 2)
        remaining_balance = round(self.data["net_spendable"] - total_spent, 2)

        start_dt = datetime.strptime(self.data["start_date"], "%Y-%m-%d")
        days_elapsed = (datetime.now() - start_dt).days
        remaining_days = self.data["total_days"] - days_elapsed

        effective_days = max(1, remaining_days)
        safe_daily_limit = round(max(0.0, remaining_balance) / effective_days, 2)

        initial_daily = (
            self.data["net_spendable"] / self.data["total_days"]
            if self.data["total_days"] > 0
            else 0
        )
        percent_left = (
            (remaining_balance / self.data["net_spendable"]) * 100
            if self.data["net_spendable"] > 0
            else 0
        )

        if remaining_balance <= 0 or percent_left <= 10:
            status = "CRITICAL"
            sub_status = "Low or Depleted Funds"
            fg_color, bg_color, bar_color = "#DC2626", "#FEE2E2", "#EF4444"
        elif percent_left <= 30 or safe_daily_limit < (initial_daily * 0.75):
            status = "CAUTION"
            sub_status = "Slow Down Daily Spending"
            fg_color, bg_color, bar_color = "#D97706", "#FEF3C7", "#F59E0B"
        else:
            status = "ON TRACK"
            sub_status = "Healthy Spending Pace"
            fg_color, bg_color, bar_color = "#16A34A", "#DCFCE7", "#22C55E"

        return {
            "total_spent": total_spent,
            "remaining_balance": remaining_balance,
            "remaining_days": remaining_days,
            "safe_daily_limit": safe_daily_limit,
            "percent_left": percent_left,
            "status": status,
            "sub_status": sub_status,
            "fg_color": fg_color,
            "bg_color": bg_color,
            "bar_color": bar_color
        }

    # ============================================
    # MAIN UI LAYOUT & NAVIGATION (UNCHANGED TABS)
    # ============================================
    def build_ui(self):
        # Top App Header
        header = tk.Frame(self.root, bg="#0F172A", padx=28, pady=14)
        header.pack(fill="x")

        title_row = tk.Frame(header, bg="#0F172A")
        title_row.pack(fill="x")

        tk.Label(
            title_row,
            text="BUDGET BALANCE",
            font=("Segoe UI", 16, "bold"),
            fg="#FFFFFF",
            bg="#0F172A"
        ).pack(side="left")

        # Window Controls on Top Right
        controls_box = tk.Frame(title_row, bg="#0F172A")
        controls_box.pack(side="right")

        self.save_badge = tk.Label(
            controls_box,
            text="● Ready",
            font=("Segoe UI", 10, "bold"),
            fg="#94A3B8",
            bg="#0F172A",
            padx=12
        )
        self.save_badge.pack(side="left")

        self.screen_btn = tk.Button(
            controls_box,
            text="Exit Fullscreen [Esc]",
            font=("Segoe UI", 9, "bold"),
            bg="#1E293B",
            fg="#E2E8F0",
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=3,
            command=self.toggle_fullscreen
        )
        self.screen_btn.pack(side="left", padx=(4, 6))

        tk.Button(
            controls_box,
            text="Close App ✕",
            font=("Segoe UI", 9, "bold"),
            bg="#DC2626",
            fg="#FFFFFF",
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=3,
            command=self.root.destroy
        ).pack(side="left")

        tk.Label(
            header,
            text="Mobile Allowance Management System • Urban College Edition",
            font=("Segoe UI", 10),
            fg="#94A3B8",
            bg="#0F172A"
        ).pack(anchor="w", pady=(2, 0))

        # Summary Dashboard Card
        dash_outer = tk.Frame(self.root, bg="#EEF2F6", padx=28, pady=12)
        dash_outer.pack(fill="x")

        self.dash_card = tk.Frame(
            dash_outer,
            bg="#FFFFFF",
            padx=20,
            pady=14,
            highlightbackground="#CBD5E1",
            highlightthickness=1
        )
        self.dash_card.pack(fill="x")

        top_dash = tk.Frame(self.dash_card, bg="#FFFFFF")
        top_dash.pack(fill="x")

        tk.Label(
            top_dash,
            text="REMAINING SPENDABLE BALANCE",
            font=("Segoe UI", 10, "bold"),
            fg="#64748B",
            bg="#FFFFFF"
        ).pack(side="left")

        self.status_pill = tk.Label(
            top_dash,
            text="NOT SET",
            font=("Segoe UI", 10, "bold"),
            fg="#475569",
            bg="#E2E8F0",
            padx=12,
            pady=3
        )
        self.status_pill.pack(side="right")

        self.balance_label = tk.Label(
            self.dash_card,
            text="₱ 0.00",
            font=("Segoe UI", 26, "bold"),
            fg="#0F172A",
            bg="#FFFFFF"
        )
        self.balance_label.pack(anchor="w", pady=(4, 8))

        # Responsive Progress Bar Canvas
        self.progress_canvas = tk.Canvas(
            self.dash_card, height=14, bg="#E2E8F0", highlightthickness=0
        )
        self.progress_canvas.pack(fill="x", pady=(0, 8))
        self.progress_rect = self.progress_canvas.create_rectangle(
            0, 0, 0, 14, fill="#22C55E", width=0
        )
        self.progress_canvas.bind("<Configure>", self.redraw_main_progress)

        # Metrics Strip
        metrics_row = tk.Frame(self.dash_card, bg="#FFFFFF")
        metrics_row.pack(fill="x")

        self.spent_label = tk.Label(
            metrics_row,
            text="Spent: ₱0.00 / ₱0.00",
            font=("Segoe UI", 10),
            fg="#475569",
            bg="#FFFFFF"
        )
        self.spent_label.pack(side="left")

        self.daily_label = tk.Label(
            metrics_row,
            text="Safe/Day: ₱0.00 (0d left)",
            font=("Segoe UI", 10, "bold"),
            fg="#0F172A",
            bg="#FFFFFF"
        )
        self.daily_label.pack(side="right")

        nav_frame = tk.Frame(self.root, bg="#EEF2F6", padx=28)
        nav_frame.pack(fill="x")

        self.nav_buttons = {}
        tabs = [
            ("setup", "Setup"),
            ("log", "Log Expense"),
            ("report", "Analytics"),
            ("history", "History")
        ]
        for key, label in tabs:
            btn = tk.Button(
                nav_frame,
                text=label,
                font=("Segoe UI", 10, "bold"),
                relief="flat",
                cursor="hand2",
                pady=9,
                command=lambda k=key: self.switch_tab(k)
            )
            btn.pack(side="left", expand=True, fill="x", padx=3)
            self.nav_buttons[key] = btn

        # Dynamic Workspace Area
        self.workspace = tk.Frame(self.root, bg="#EEF2F6", padx=28, pady=12)
        self.workspace.pack(fill="both", expand=True)

        # Bottom Live System Process Trace Panel
        trace_outer = tk.Frame(self.root, bg="#0F172A", padx=28, pady=10)
        trace_outer.pack(fill="x", side="bottom")

        tk.Label(
            trace_outer,
            text="LIVE SYSTEM PROCESS TRACE",
            font=("Consolas", 9, "bold"),
            fg="#38BDF8",
            bg="#0F172A"
        ).pack(anchor="w")

        self.trace_text = tk.Text(
            trace_outer,
            height=4,
            font=("Consolas", 10),
            bg="#020617",
            fg="#A7F3D0",
            relief="flat",
            wrap="word",
            state="disabled"
        )
        self.trace_text.pack(fill="x", pady=(4, 0))

    def redraw_main_progress(self, event=None):
        width = self.progress_canvas.winfo_width()
        ratio = max(0.0, min(1.0, self.current_pct_left / 100.0))
        bar_width = int(width * ratio)
        self.progress_canvas.coords(self.progress_rect, 0, 0, bar_width, 14)
        self.progress_canvas.itemconfig(self.progress_rect, fill=self.current_bar_color)

    def log_process(self, module_tag, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        line = f"[{timestamp}] [{module_tag}] {message}\n"
        self.trace_text.config(state="normal")
        self.trace_text.insert("end", line)
        self.trace_text.see("end")
        self.trace_text.config(state="disabled")

    def refresh_dashboard(self):
        if not self.data["is_configured"]:
            self.status_pill.config(text="SETUP REQUIRED", fg="#1E40AF", bg="#DBEAFE")
            self.balance_label.config(text="₱ 0.00")
            self.spent_label.config(text="Spent: ₱0.00 / ₱0.00")
            self.daily_label.config(text="Safe/Day: ₱0.00 (0 days)")
            self.current_pct_left = 0.0
            self.redraw_main_progress()
            return

        m = self.get_budget_metrics()
        self.status_pill.config(
            text=f"{m['status']} ({m['percent_left']:.0f}%)",
            fg=m["fg_color"],
            bg=m["bg_color"]
        )
        self.balance_label.config(text=f"₱ {m['remaining_balance']:,.2f}")
        self.spent_label.config(
            text=f"Spent: ₱{m['total_spent']:,.2f} / ₱{self.data['net_spendable']:,.2f}"
        )
        days_txt = f"{m['remaining_days']}d left" if m["remaining_days"] > 0 else "Final day"
        self.daily_label.config(text=f"Budget/Day: ₱{m['safe_daily_limit']:,.2f} ({days_txt})")

        self.current_pct_left = m["percent_left"]
        self.current_bar_color = m["bar_color"]
        self.redraw_main_progress()

    def switch_tab(self, tab_key):
        self.active_tab = tab_key
        for key, btn in self.nav_buttons.items():
            if key == tab_key:
                btn.config(bg="#2563EB", fg="#FFFFFF")
            else:
                btn.config(bg="#CBD5E1", fg="#1E293B")

        for widget in self.workspace.winfo_children():
            widget.destroy()

        if tab_key == "setup":
            self.render_setup_tab()
        elif tab_key == "log":
            self.render_log_tab()
        elif tab_key == "report":
            self.render_report_tab()
        elif tab_key == "history":
            self.render_history_tab()

    # ============================================
    # TAB 1: ALLOWANCE & FIXED-COST SETUP
    # ============================================
    def render_setup_tab(self):
        card = tk.Frame(
            self.workspace, bg="#FFFFFF", padx=22, pady=18,
            highlightbackground="#CBD5E1", highlightthickness=1
        )
        card.pack(fill="both", expand=True)

        tk.Label(
            card, text="ALLOWANCE & FIXED DEDUCTIONS",
            font=("Segoe UI", 11, "bold"), fg="#0F172A", bg="#FFFFFF"
        ).pack(anchor="w", pady=(0, 12))

        self.total_var = tk.StringVar(
            value=str(self.data["total_allowance"]) if self.data["is_configured"] else "2500"
        )
        self.deduct_var = tk.StringVar(
            value=str(self.data["fixed_deductions"]) if self.data["is_configured"] else "500"
        )
        self.days_var = tk.StringVar(
            value=str(self.data["total_days"]) if self.data["is_configured"] else "7"
        )

        form = tk.Frame(card, bg="#FFFFFF")
        form.pack(fill="x")

        tk.Label(form, text="Total Allowance (₱):", font=("Segoe UI", 10, "bold"), bg="#FFFFFF", fg="#334155").grid(row=0, column=0, sticky="w", pady=6)
        tk.Entry(form, textvariable=self.total_var, font=("Segoe UI", 11), width=26, relief="solid", bd=1).grid(row=0, column=1, sticky="e", pady=6)

        tk.Label(form, text="Fixed Deductions (Rent/Bills):", font=("Segoe UI", 10, "bold"), bg="#FFFFFF", fg="#334155").grid(row=1, column=0, sticky="w", pady=6)
        tk.Entry(form, textvariable=self.deduct_var, font=("Segoe UI", 11), width=26, relief="solid", bd=1).grid(row=1, column=1, sticky="e", pady=6)

        tk.Label(form, text="Cycle Duration (Days):", font=("Segoe UI", 10, "bold"), bg="#FFFFFF", fg="#334155").grid(row=2, column=0, sticky="w", pady=6)
        days_box = tk.Frame(form, bg="#FFFFFF")
        days_box.grid(row=2, column=1, sticky="e", pady=6)
        tk.Entry(days_box, textvariable=self.days_var, font=("Segoe UI", 11), width=10, relief="solid", bd=1).pack(side="left", padx=(0, 6))

        for d in (7, 15, 30):
            tk.Button(
                days_box, text=f"{d} Days", font=("Segoe UI", 9, "bold"),
                bg="#E2E8F0", fg="#1E293B", relief="flat", cursor="hand2", padx=8, pady=2,
                command=lambda val=str(d): self.days_var.set(val)
            ).pack(side="left", padx=2)

        form.columnconfigure(0, weight=1)

        # Live Formula Process Box
        formula_box = tk.Frame(card, bg="#F8FAFC", padx=14, pady=12, highlightbackground="#CBD5E1", highlightthickness=1)
        formula_box.pack(fill="x", pady=14)

        tk.Label(
            formula_box, text="CALCULATION PROCESS:",
            font=("Segoe UI", 9, "bold"), fg="#2563EB", bg="#F8FAFC"
        ).pack(anchor="w")

        self.setup_preview_lbl = tk.Label(
            formula_box, text="", font=("Consolas", 10), fg="#1E293B", bg="#F8FAFC", justify="left"
        )
        self.setup_preview_lbl.pack(anchor="w", pady=(4, 0))

        for var in (self.total_var, self.deduct_var, self.days_var):
            var.trace_add("write", lambda *_: self.update_setup_preview())
        self.update_setup_preview()

        tk.Button(
            card,
            text="PROCEED →",
            font=("Segoe UI", 11, "bold"),
            bg="#16A34A",
            fg="#FFFFFF",
            relief="flat",
            cursor="hand2",
            pady=11,
            command=self.handle_setup_save
        ).pack(fill="x", side="bottom")

    def update_setup_preview(self):
        try:
            total = float(self.total_var.get())
            deduct = float(self.deduct_var.get())
            days = int(self.days_var.get())
            if total <= 0 or deduct < 0 or deduct >= total or days < 1:
                raise ValueError
            net = total - deduct
            daily = net / days
            text = (
                f"Net Spendable = ₱{total:,.2f} - ₱{deduct:,.2f} = ₱{net:,.2f}\n"
                f"Daily Target  = ₱{net:,.2f} ÷ {days} days = ₱{daily:,.2f}/day"
            )
        except ValueError:
            text = "Enter valid positive numbers (Deductions < Total)."
        self.setup_preview_lbl.config(text=text)

    def handle_setup_save(self):
        try:
            total = round(float(self.total_var.get()), 2)
            deduct = round(float(self.deduct_var.get()), 2)
            days = int(self.days_var.get())
        except ValueError:
            messagebox.showerror("Input Validation Error", "Please enter valid numeric values.")
            return

        if total <= 0:
            messagebox.showerror("Input Validation Error", "Total allowance must be greater than ₱0.")
            return
        if deduct < 0 or deduct >= total:
            messagebox.showerror("Input Validation Error", "Deductions must be ₱0 or less than Total Allowance.")
            return
        if not (1 <= days <= 365):
            messagebox.showerror("Input Validation Error", "Cycle duration must be between 1 and 365 days.")
            return

        if self.data["is_configured"] and self.data["expenses"]:
            if not messagebox.askyesno("Reset Cycle?", "Starting a new cycle will clear previous expense logs. Continue?"):
                return

        net = round(total - deduct, 2)
        self.data.update({
            "is_configured": True,
            "total_allowance": total,
            "fixed_deductions": deduct,
            "net_spendable": net,
            "total_days": days,
            "start_date": datetime.now().strftime("%Y-%m-%d"),
            "expenses": []
        })
        self.save_data()
        self.refresh_dashboard()
        self.log_process(
            "MODULE 3: SETUP",
            f"Net Spendable = ₱{net:,.2f} | Target = ₱{net/days:,.2f}/day ({days}d)"
        )
        self.switch_tab("log")

    # ============================================
    # TAB 2: LOG EXPENSE WITH LIVE IMPACT PREVIEW
    # ============================================
    def render_log_tab(self):
        card = tk.Frame(
            self.workspace, bg="#FFFFFF", padx=22, pady=18,
            highlightbackground="#CBD5E1", highlightthickness=1
        )
        card.pack(fill="both", expand=True)

        if not self.data["is_configured"]:
            tk.Label(
                card, text="Please complete Setup Allowance first.",
                font=("Segoe UI", 11), fg="#DC2626", bg="#FFFFFF"
            ).pack(pady=40)
            return

        tk.Label(
            card, text="LOG DAILY STUDENT EXPENSE",
            font=("Segoe UI", 11, "bold"), fg="#0F172A", bg="#FFFFFF"
        ).pack(anchor="w", pady=(0, 10))

        # Quick-Tap Urban Student Presets
        preset_frame = tk.Frame(card, bg="#FFFFFF")
        preset_frame.pack(fill="x", pady=(0, 12))
        for item_name, cat_name in QUICK_PRESETS:
            tk.Button(
                preset_frame,
                text=item_name,
                font=("Segoe UI", 9, "bold"),
                bg="#EFF6FF",
                fg="#1D4ED8",
                relief="flat",
                cursor="hand2",
                pady=5,
                command=lambda n=item_name, c=cat_name: self.apply_preset(n, c)
            ).pack(side="left", expand=True, fill="x", padx=3)

        form = tk.Frame(card, bg="#FFFFFF")
        form.pack(fill="x")

        self.cat_var = tk.StringVar(value=CATEGORIES[0])
        self.note_var = tk.StringVar()
        self.amt_var = tk.StringVar()

        tk.Label(form, text="Expense Category:", font=("Segoe UI", 10, "bold"), bg="#FFFFFF", fg="#334155").grid(row=0, column=0, sticky="w", pady=6)
        cat_menu = tk.OptionMenu(form, self.cat_var, *CATEGORIES)
        cat_menu.config(font=("Segoe UI", 10), bg="#F1F5F9", relief="flat", width=24)
        cat_menu["menu"].config(font=("Segoe UI", 10))
        cat_menu.grid(row=0, column=1, sticky="e", pady=6)

        tk.Label(form, text="Description:", font=("Segoe UI", 10, "bold"), bg="#FFFFFF", fg="#334155").grid(row=1, column=0, sticky="w", pady=6)
        tk.Entry(form, textvariable=self.note_var, font=("Segoe UI", 11), width=28, relief="solid", bd=1).grid(row=1, column=1, sticky="e", pady=6)

        tk.Label(form, text="Amount Spent (₱):", font=("Segoe UI", 10, "bold"), bg="#FFFFFF", fg="#334155").grid(row=2, column=0, sticky="w", pady=6)
        tk.Entry(form, textvariable=self.amt_var, font=("Segoe UI", 11), width=28, relief="solid", bd=1).grid(row=2, column=1, sticky="e", pady=6)

        form.columnconfigure(0, weight=1)

        # Live Impact Preview Box
        impact_box = tk.Frame(card, bg="#F8FAFC", padx=14, pady=12, highlightbackground="#CBD5E1", highlightthickness=1)
        impact_box.pack(fill="x", pady=14)

        tk.Label(
            impact_box, text="BALANCE PREVIEW:",
            font=("Segoe UI", 9, "bold"), fg="#2563EB", bg="#F8FAFC"
        ).pack(anchor="w")

        self.impact_lbl = tk.Label(
            impact_box, text="", font=("Consolas", 10), fg="#1E293B", bg="#F8FAFC", justify="left"
        )
        self.impact_lbl.pack(anchor="w", pady=(4, 0))

        self.amt_var.trace_add("write", lambda *_: self.update_expense_preview())
        self.update_expense_preview()

        tk.Button(
            card,
            text="RECORD",
            font=("Segoe UI", 11, "bold"),
            bg="#2563EB",
            fg="#FFFFFF",
            relief="flat",
            cursor="hand2",
            pady=11,
            command=self.handle_log_expense
        ).pack(fill="x", side="bottom")

    def apply_preset(self, item_name, cat_name):
        self.note_var.set(item_name)
        self.cat_var.set(cat_name)
        self.log_process("UI PRESET", f"Selected '{item_name}' under [{cat_name}].")

    def update_expense_preview(self):
        m = self.get_budget_metrics()
        curr = m["remaining_balance"]
        try:
            amt = float(self.amt_var.get())
            if amt <= 0:
                raise ValueError
            proj = curr - amt
            pct = (proj / self.data["net_spendable"]) * 100 if self.data["net_spendable"] > 0 else 0
            next_state = "CRITICAL" if (proj <= 0 or pct <= 10) else ("CAUTION" if pct <= 30 else "ON TRACK")
            text = (
                f"Current: ₱{curr:,.2f}  ->  After: ₱{proj:,.2f}\n"
                f"Projected Health: {pct:.1f}% left ({next_state})"
            )
        except ValueError:
            text = f"Current Available: ₱{curr:,.2f}\nEnter an amount above to preview balance."
        self.impact_lbl.config(text=text)

    def handle_log_expense(self):
        try:
            amt = round(float(self.amt_var.get()), 2)
        except ValueError:
            messagebox.showerror("Input Validation Error", "Please enter a valid numeric amount.")
            return

        if amt <= 0:
            messagebox.showerror("Input Validation Error", "Expense amount must be greater than ₱0.")
            return

        m = self.get_budget_metrics()
        if amt > m["remaining_balance"]:
            if not messagebox.askyesno(
                "Overdraft Warning",
                f"₱{amt:,.2f} exceeds your remaining ₱{m['remaining_balance']:,.2f}.\nLog anyway?"
            ):
                return

        cat = self.cat_var.get()
        note = self.note_var.get().strip() or "General Student Expense"

        entry = {
            "id": len(self.data["expenses"]) + 1,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "category": cat,
            "note": note,
            "amount": amt
        }
        self.data["expenses"].append(entry)
        self.save_data()
        self.refresh_dashboard()

        updated_m = self.get_budget_metrics()
        self.log_process(
            "MODULE 5: LOG",
            f"Saved ₱{amt:,.2f} [{cat}] | Status -> {updated_m['status']}"
        )

        self.note_var.set("")
        self.amt_var.set("")
        self.update_expense_preview()

    # ============================================
    # TAB 3: CATEGORY ANALYTICS BREAKDOWN
    # ============================================
    def render_report_tab(self):
        card = tk.Frame(
            self.workspace, bg="#FFFFFF", padx=22, pady=18,
            highlightbackground="#CBD5E1", highlightthickness=1
        )
        card.pack(fill="both", expand=True)

        tk.Label(
            card, text="CATEGORY SPENDING ANALYTICS",
            font=("Segoe UI", 11, "bold"), fg="#0F172A", bg="#FFFFFF"
        ).pack(anchor="w", pady=(0, 12))

        total_spent = sum(item["amount"] for item in self.data["expenses"])

        for cat in CATEGORIES:
            cat_sum = sum(item["amount"] for item in self.data["expenses"] if item["category"] == cat)
            pct = (cat_sum / total_spent * 100) if total_spent > 0 else 0.0

            row = tk.Frame(card, bg="#FFFFFF")
            row.pack(fill="x", pady=7)

            lbl_row = tk.Frame(row, bg="#FFFFFF")
            lbl_row.pack(fill="x")

            tk.Label(
                lbl_row, text=cat, font=("Segoe UI", 10, "bold"), fg="#1E293B", bg="#FFFFFF"
            ).pack(side="left")

            tk.Label(
                lbl_row, text=f"₱{cat_sum:,.2f} ({pct:.1f}%)",
                font=("Segoe UI", 10, "bold"), fg="#475569", bg="#FFFFFF"
            ).pack(side="right")

            bar_bg = tk.Canvas(row, height=14, bg="#E2E8F0", highlightthickness=0)
            bar_bg.pack(fill="x", pady=(4, 0))
            rect = bar_bg.create_rectangle(0, 0, 0, 14, fill=CATEGORY_COLORS[cat], width=0)

            def draw_bar(event, canvas=bar_bg, item_id=rect, ratio=pct / 100.0):
                canvas.coords(item_id, 0, 0, int(event.width * ratio), 14)

            bar_bg.bind("<Configure>", draw_bar)

        self.log_process("MODULE 4: REPORT", f"Rendered category breakdown (Total: ₱{total_spent:,.2f}).")

# ============================================
    # TAB 4: TRANSACTION HISTORY & DELETION
    # ============================================
    def render_history_tab(self):
        card = tk.Frame(
            self.workspace, bg="#FFFFFF", padx=22, pady=18,
            highlightbackground="#CBD5E1", highlightthickness=1
        )
        card.pack(fill="both", expand=True)

        tk.Label(
            card, text="TRANSACTION LEDGER",
            font=("Segoe UI", 11, "bold"), fg="#0F172A", bg="#FFFFFF"
        ).pack(anchor="w", pady=(0, 10))

        list_frame = tk.Frame(card, bg="#FFFFFF")
        list_frame.pack(fill="both", expand=True)

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")

        self.history_listbox = tk.Listbox(
            list_frame,
            font=("Consolas", 10),
            bg="#F8FAFC",
            fg="#0F172A",
            selectbackground="#DBEAFE",
            selectforeground="#1E3A8A",
            relief="solid",
            bd=1,
            yscrollcommand=scrollbar.set
        )
        self.history_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.history_listbox.yview)

        self.populate_history_listbox()

        tk.Button(
            card,
            text="Delete Selected Transaction",
            font=("Segoe UI", 10, "bold"),
            bg="#DC2626",
            fg="#FFFFFF",
            relief="flat",
            cursor="hand2",
            pady=10,
            command=self.handle_delete_selected
        ).pack(fill="x", pady=(12, 0))

    def populate_history_listbox(self):
        """Clears and refreshes the existing ledger list in place."""
        self.history_listbox.delete(0, "end")
        if not self.data["expenses"]:
            self.history_listbox.insert("end", " No transactions recorded yet.")
        else:
            for item in self.data["expenses"]:
                line = (
                    f" #{item['id']:<3} | {item['date']} | "
                    f"₱{item['amount']:>8,.2f} | {item['category']:<17} | {item['note']}"
                )
                self.history_listbox.insert("end", line)

    def handle_delete_selected(self):
        if not self.data["expenses"]:
            return
        selection = self.history_listbox.curselection()
        if not selection:
            messagebox.showinfo("Select Item", "Click a transaction in the list first to delete it.")
            return

        idx = selection[0]
        removed = self.data["expenses"].pop(idx)
        for new_id, item in enumerate(self.data["expenses"], start=1):
            item["id"] = new_id

        self.save_data()
        self.refresh_dashboard()
        self.populate_history_listbox()
        self.log_process(
            "MODULE 5: DELETE",
            f"Removed '{removed['note']}' (₱{removed['amount']:,.2f}) & recalculated."
        )


if __name__ == "__main__":
    root = tk.Tk()
    app = BudgetBalanceApp(root)
    root.mainloop()