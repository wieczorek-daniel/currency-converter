import os
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from ttkbootstrap import Style
from bs4 import BeautifulSoup
import requests
import re


def currencies_web_scraping():
    page_url = "https://www.nbp.pl/"
    page = requests.get(page_url)
    soup = BeautifulSoup(page.content, "html.parser")

    search_text = re.compile(r"Tabela z dnia [0-9]", re.IGNORECASE)
    found_text = soup.find("div", text=search_text)
    update_date_regex = re.compile(r"\d{4}-\d{2}-\d{2}", re.IGNORECASE)
    update_date = update_date_regex.findall(found_text.text)[0]

    # Find the first <table> tag that follows found_text
    currencies_table = found_text.findNext("table")
    currencies_data = []
    rows = currencies_table.find_all("tr")
    for tr_number, tr in enumerate(rows):
        cols = tr.find_all("td")
        currency_data = []
        for td_number, td in enumerate(cols):
            currency_data.append(float(td.text.replace(",", ".")) if "," in td.text else td.text)
        currencies_data.append(currency_data)

    return update_date, currencies_data


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Currency Converter")
        self.resizable(0, 0)

        # Window center
        window_width = 800
        window_height = 400
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x_coordinate = int((screen_width/2)-(window_width/2))
        y_coordinate = int((screen_height/2)-(window_height/2))
        self.geometry(f"{window_width}x{window_height}+{x_coordinate}+{y_coordinate}")

        # Icon made by photo3idea_studio from www.flaticon.com
        if "nt" == os.name:
            self.iconbitmap("icons/icon.ico")
        else:
            img = tk.PhotoImage(file="icons/icon.png")
            self.tk.call("wm", "iconphoto", self._w, img)
        Style(theme="flatly")

        # Create grid
        for index in range(5):
            self.columnconfigure(index=index, weight=1)
        for index in range(2):
            self.rowconfigure(index=index, weight=2 if index == 0 else 1)

        self.from_value, self.from_currency, self.to_value, self.to_currency, self.currencies_data = \
            self.create_widgets()

    def create_widgets(self):
        font_parameters = ("roboto", 16, "bold")

        currencies_scraper = currencies_web_scraping()
        table_label = tk.Label(text=f"Table of {currencies_scraper[0]}\nData source: National Bank of Poland",
                               font=font_parameters)
        table_label.grid(column=0, row=0, columnspan=5, sticky=tk.N, pady=30)

        table = ttk.Treeview(self, column=("currency", "value"), show="headings", height=5)
        table.column("currency", anchor=tk.CENTER)
        table.heading("currency", text="Currency")
        table.column("value", anchor=tk.CENTER)
        table.heading("value", text="Mid-rate [PLN]")

        currencies_data = currencies_scraper[1]
        for id, (currency, mid_rate) in enumerate(currencies_data):
            table.insert("", index=id, values=(currency, mid_rate))

        table.grid(column=0, row=0, columnspan=5, pady=30)

        currencies = ["PLN"] + ["".join(filter(str.isalpha, currency_data[0])) for currency_data in currencies_data]

        from_label = tk.Label(text="From:", font=font_parameters)
        from_label.grid(column=0, row=1, sticky=tk.NW, padx=(21, 0))
        from_value = tk.Entry(width=10, borderwidth=1, font=font_parameters, justify='center')
        from_value.grid(column=0, row=1, ipady=4)

        from_currency = ttk.Combobox(width=5, justify="center", state="readonly", font=font_parameters)
        from_currency["values"] = currencies
        from_currency.grid(column=1, row=1, sticky=tk.W)
        from_currency.current(0)

        calculate_button = tk.Button(text="Calculate", command=self.calculate, font=font_parameters, borderwidth=2)
        calculate_button.grid(column=2, row=1)

        to_label = tk.Label(text="To:", font=font_parameters)
        to_label.grid(column=3, row=1, sticky=tk.NW, padx=(47, 0))
        to_value = tk.Entry(width=10, borderwidth=1, font=font_parameters, justify='center', state="readonly")
        to_value.grid(column=3, row=1, ipady=4, sticky=tk.E)

        to_currency = ttk.Combobox(width=5, justify="center", state="readonly", font=font_parameters)
        to_currency["values"] = currencies
        to_currency.grid(column=4, row=1)
        to_currency.current(0)

        return from_value, from_currency, to_value, to_currency, currencies_data

    def calculate(self):
        self.to_value.config(state="normal")
        self.to_value.delete(0, tk.END)

        # Input validation
        try:
            float(self.from_value.get())
        except ValueError:
            if not self.from_value.get():
                error_message = "Input value is empty."
            else:
                error_message = "Invalid format for input value.\nUse numeric input (examples: 123 or 123.45)"
            messagebox.showerror(title="Error during calculation", message=error_message)
            return

        # Calculation
        final_value = 0
        if self.from_currency.get() == self.to_currency.get():
            final_value = float(self.from_value.get())
        elif self.from_currency.get() == "PLN":
            for currency, mid_rate in self.currencies_data:
                if self.to_currency.get() in currency:
                    final_value = float(self.from_value.get()) / (
                        (mid_rate / 100) if self.to_currency.get() == "JPY" else mid_rate)
        elif self.to_currency.get() == "PLN":
            for currency, mid_rate in self.currencies_data:
                if self.from_currency.get() in currency:
                    final_value = float(self.from_value.get()) * (
                        (mid_rate / 100) if self.from_currency.get() == "JPY" else mid_rate)
        else:
            from_mid_rate = to_mid_rate = 0
            for currency, mid_rate in self.currencies_data:
                if self.from_currency.get() in currency:
                    from_mid_rate = mid_rate
                if self.to_currency.get() in currency:
                    to_mid_rate = mid_rate
            final_value = (float(self.from_value.get()) * (
                (from_mid_rate / 100) if self.from_currency.get() == "JPY" else from_mid_rate)) / (
                              (to_mid_rate / 100) if self.to_currency.get() == "JPY" else to_mid_rate)

        self.to_value.insert(0, round(final_value, 2))
        self.to_value.config(state="disable")


if __name__ == "__main__":
    app = App()
    app.mainloop()
