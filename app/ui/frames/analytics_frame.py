import customtkinter as ctk
import tkinter as tk
from collections import Counter
from datetime import datetime

# --- MATPLOTLIB IMPORTS ---
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.patches import Circle # Import Circle directly

from app.core.data_handler import DataHandler

class AnalyticsFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        
        # Grid layout for the main frame
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1) # Charts area expands

        self.setup_ui()

    def setup_ui(self):
        # --- 1. Toolbar ---
        tool_an = ctk.CTkFrame(self, fg_color="transparent")
        tool_an.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        
        ctk.CTkLabel(tool_an, text="Live Intelligence Dashboard", font=("Roboto", 16, "bold"), text_color="white").pack(side="left")
        ctk.CTkButton(tool_an, text="↻ Refresh Analytics", command=self.update_charts, width=120, fg_color="#333", hover_color="#444").pack(side="right")

        # --- 2. Scrollable Container for Charts ---
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.grid(row=1, column=0, sticky="nsew")
        self.scroll_frame.grid_columnconfigure((0, 1), weight=1) # 2 Column Layout

        # Placeholders for content
        self.kpi_container = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        self.kpi_container.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 20))
        
        self.chart_frame_1 = ctk.CTkFrame(self.scroll_frame, fg_color="#2b2b2b", corner_radius=10)
        self.chart_frame_1.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        
        self.chart_frame_2 = ctk.CTkFrame(self.scroll_frame, fg_color="#2b2b2b", corner_radius=10)
        self.chart_frame_2.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)

        self.chart_frame_3 = ctk.CTkFrame(self.scroll_frame, fg_color="#2b2b2b", corner_radius=10)
        self.chart_frame_3.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=10, pady=10)

    def update_charts(self):
        """Main method to calculate data and redraw everything."""
        # 1. Clear previous widgets
        for widget in self.kpi_container.winfo_children(): widget.destroy()
        for widget in self.chart_frame_1.winfo_children(): widget.destroy()
        for widget in self.chart_frame_2.winfo_children(): widget.destroy()
        for widget in self.chart_frame_3.winfo_children(): widget.destroy()

        # 2. Load Data
        data = DataHandler.load_data()
        
        if not data:
            ctk.CTkLabel(self.kpi_container, text="No Data Available. Import resources to see analytics.", font=("Roboto", 14)).pack(pady=20)
            return

        # 3. Process Data
        cats, provs, all_tags, dates = [], [], [], []
        
        for row in data:
            # Categories
            c = str(row.get('category', '')).strip()
            # If category is empty, try to infer from tags
            if not c and row.get('tech_tags'):
                clean_t = str(row['tech_tags']).replace("['", "").replace("']", "").split(',')[0]
                c = clean_t
            if c: cats.append(c)

            # Providers
            p = str(row.get('provider', '')).strip()
            if p: provs.append(p)

            # Tags (Cleaning the messy "['tag']" format)
            t_raw = (str(row.get('tech_tags', '')) + "," + str(row.get('tags', '')))
            t_clean = t_raw.replace("['", "").replace("']", "").replace("'", "").replace('"', "")
            for tag in t_clean.split(','):
                tag = tag.strip()
                if tag: all_tags.append(tag)

            # Dates (for timeline)
            d_raw = str(row.get('created_at', ''))
            if d_raw:
                try:
                    # Parse ISO format, just keep YYYY-MM-DD
                    dt = datetime.fromisoformat(d_raw).strftime('%Y-%m-%d')
                    dates.append(dt)
                except: pass

        # 4. Generate KPIs
        cat_counts = Counter(cats)
        prov_counts = Counter(provs)
        tag_counts = Counter(all_tags)
        
        top_cat = cat_counts.most_common(1)[0][0] if cats else "N/A"
        top_prov = prov_counts.most_common(1)[0][0] if provs else "N/A"

        self._create_kpi_card(self.kpi_container, "Total Resources", str(len(data)), "#3B8ED0", 0)
        self._create_kpi_card(self.kpi_container, "Top Category", top_cat, "#2CC985", 1)
        self._create_kpi_card(self.kpi_container, "Top Provider", top_prov, "#E09F3E", 2)
        self._create_kpi_card(self.kpi_container, "Unique Tags", str(len(tag_counts)), "#9B59B6", 3)

        # 5. Draw Charts
        self._draw_donut_chart(cat_counts, self.chart_frame_1, "Category Distribution")
        self._draw_bar_chart(prov_counts, self.chart_frame_2, "Top 5 Providers")
        self._draw_timeline_chart(dates, self.chart_frame_3, "Resources Added Over Time")

    def _create_kpi_card(self, parent, title, value, color, col_idx):
        card = ctk.CTkFrame(parent, fg_color="#212121", border_width=2, border_color="#333", corner_radius=10)
        card.grid(row=0, column=col_idx, padx=5, sticky="ew")
        parent.grid_columnconfigure(col_idx, weight=1)

        ctk.CTkLabel(card, text=title, font=("Roboto", 11), text_color="#aaa").pack(pady=(10, 0))
        ctk.CTkLabel(card, text=str(value)[:18], font=("Roboto", 22, "bold"), text_color=color).pack(pady=(0, 10))

    def _draw_donut_chart(self, counter, frame, title):
        if not counter:
            ctk.CTkLabel(frame, text="No category data", font=("Roboto", 12), text_color="#aaa").pack(padx=16, pady=16)
            return

        try:
            # Calculate Sizes (top 5 + Other)
            common = counter.most_common(5)
            labels = [x[0] for x in common]
            sizes = [x[1] for x in common]

            remaining = sum(counter.values()) - sum(sizes)
            if remaining > 0:
                labels.append("Other")
                sizes.append(remaining)

            # Protection against zero data
            if sum(sizes) == 0:
                ctk.CTkLabel(frame, text="No category data", font=("Roboto", 12), text_color="#aaa").pack(padx=16, pady=16)
                return

            # Setup Figure
            fig = Figure(figsize=(5, 4), dpi=100)
            fig.patch.set_facecolor('#2b2b2b')
            ax = fig.add_subplot(111)
            ax.set_facecolor('#2b2b2b')

            # Colors - cycle if there are more labels
            base_colors = ['#3B8ED0', '#2CC985', '#E09F3E', '#9B59B6', '#E74C3C', '#95A5A6']
            import itertools
            colors = [c for _, c in zip(range(len(labels)), itertools.cycle(base_colors))]

            # Draw Pie
            wedges, texts, autotexts = ax.pie(
                sizes, labels=labels, autopct='%1.1f%%', startangle=90,
                colors=colors, pctdistance=0.85, textprops={'color': 'white'}
            )

            # Draw Center Circle (Donut)
            centre_circle = Circle((0, 0), 0.70, fc='#2b2b2b', zorder=10)
            ax.add_patch(centre_circle)
            ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.

            # Styling (ensure colors for texts)
            for t in texts:
                t.set_color('white')
            for t in autotexts:
                t.set_color('white')

            # Legend on the side to clarify small slices
            try:
                ax.legend(labels, loc='upper left', bbox_to_anchor=(1, 0.9), frameon=False, prop={'size': 8})
            except Exception:
                pass

            ax.set_title(title, color='white', pad=20)

            canvas = FigureCanvasTkAgg(fig, master=frame)
            canvas.draw_idle()
            widget = canvas.get_tk_widget()
            widget.pack(fill="both", expand=True)
            try:
                widget.configure(bg='#2b2b2b')
            except Exception:
                pass

        except Exception as e:
            print(f"❌ Analytics Chart Error (donut): {e}")

    def _draw_bar_chart(self, counter, frame, title):
        if not counter: return
        
        common = counter.most_common(5)
        labels = [x[0] for x in common]
        values = [x[1] for x in common]

        if not values: return

        fig = Figure(figsize=(5, 4), dpi=100)
        fig.patch.set_facecolor('#2b2b2b')
        ax = fig.add_subplot(111)
        ax.set_facecolor('#2b2b2b')

        y_pos = range(len(labels))
        ax.barh(y_pos, values, align='center', color='#3B8ED0')
        ax.set_yticks(y_pos)
        ax.set_yticklabels(labels, color='white')
        ax.invert_yaxis()  # labels read top-to-bottom
        ax.set_title(title, color='white')

        # Styling
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_color('#555')
        ax.spines['left'].set_color('#555')
        ax.tick_params(axis='x', colors='white')
        
        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def _draw_timeline_chart(self, dates, frame, title):
        if not dates: return

        # Count per date
        date_counts = Counter(dates)
        sorted_dates = sorted(date_counts.keys())
        counts = [date_counts[d] for d in sorted_dates]
        
        if not counts: return

        fig = Figure(figsize=(8, 3), dpi=100)
        fig.patch.set_facecolor('#2b2b2b')
        ax = fig.add_subplot(111)
        ax.set_facecolor('#2b2b2b')

        ax.plot(sorted_dates, counts, marker='o', linestyle='-', color='#2CC985', linewidth=2)
        ax.fill_between(sorted_dates, counts, color='#2CC985', alpha=0.3)

        ax.set_title(title, color='white')
        
        # Grid
        ax.grid(color='#444', linestyle='--', linewidth=0.5)
        
        # Styling
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_color('white')
        ax.spines['left'].set_color('white')
        ax.tick_params(axis='x', colors='white', rotation=45)
        ax.tick_params(axis='y', colors='white')

        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)