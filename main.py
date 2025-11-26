import base64
import tkinter as tk
from tkinter import messagebox
from typing import Optional

import requests

try:
    from api_config import API_KEY
except ImportError:
    API_KEY = ""

API_URL = "https://api.weatherapi.com/v1/current.json"

class RoundedCard(tk.Canvas):
    """A simple rounded card with a shadow and an inner frame for content."""

    def __init__(
        self,
        parent: tk.Misc,
        width: int,
        fg_color: str,
        shadow_color: str,
        bg_color: str,
        radius: int = 16,
        padding: int = 16,
    ) -> None:
        super().__init__(parent, width=width, highlightthickness=0, bd=0, bg=bg_color)
        self.radius = radius
        self.fg_color = fg_color
        self.shadow_color = shadow_color
        self.bg_color = bg_color
        self.padding = padding

        self.inner = tk.Frame(self, bg=fg_color)
        self.create_window((padding, padding), window=self.inner, anchor="nw", tags=("inner",))

        self.bind("<Configure>", self._redraw)
        self.inner.bind("<Configure>", self._resize_to_inner)

    def _rounded_polygon(self, x1: int, y1: int, x2: int, y2: int, radius: int, fill: str, tag: str) -> None:
        points = [
            x1 + radius, y1,
            x2 - radius, y1,
            x2, y1,
            x2, y1 + radius,
            x2, y2 - radius,
            x2, y2,
            x2 - radius, y2,
            x1 + radius, y2,
            x1, y2,
            x1, y2 - radius,
            x1, y1 + radius,
            x1, y1,
        ]
        self.create_polygon(
            points,
            smooth=True,
            splinesteps=32,
            fill=fill,
            outline="",
            tags=tag,
        )

    def _redraw(self, event: Optional[tk.Event] = None) -> None:
        self.delete("card")
        w = self.winfo_width()
        h = self.winfo_height()
        r = min(self.radius, w // 2, h // 2)
        offset = 6
        # Shadow
        self._rounded_polygon(offset, offset, w - 1, h - 1, r, self.shadow_color, "card")
        # Foreground card
        self._rounded_polygon(0, 0, w - offset, h - offset, r, self.fg_color, "card")
        self.coords("inner", self.padding, self.padding)

    def _resize_to_inner(self, event: tk.Event) -> None:
        width = event.width + self.padding * 2
        height = event.height + self.padding * 2
        self.config(width=width, height=height)
        self._redraw()


class RoundedEntry(tk.Frame):
    """A rounded input field with a subtle shadow."""

    def __init__(
        self,
        parent: tk.Misc,
        font_family: str,
        text_color: str,
        bg_color: str,
        input_bg: str,
        shadow_color: str,
        radius: int = 12,
        padding: int = 10,
    ) -> None:
        super().__init__(parent, bg=bg_color, highlightthickness=0, bd=0)
        self.radius = radius
        self.padding = padding
        self.bg_color = bg_color
        self.input_bg = input_bg
        self.shadow_color = shadow_color
        self.text_color = text_color

        self.canvas = tk.Canvas(self, height=radius * 2 + padding * 2, bg=bg_color, highlightthickness=0, bd=0)
        self.canvas.pack(fill="x", expand=True)

        self.entry = tk.Entry(
            self,
            bg=input_bg,
            fg=text_color,
            insertbackground=text_color,
            relief="flat",
            font=(font_family, 12),
            bd=0,
            highlightthickness=0,
        )
        self.canvas.create_window((padding + radius, (radius * 2 + padding * 2) / 2), window=self.entry, anchor="w", tags="entry")
        self.canvas.bind("<Configure>", self._redraw)

    def _rounded_polygon(self, canvas: tk.Canvas, x1: int, y1: int, x2: int, y2: int, radius: int, fill: str, tag: str) -> None:
        points = [
            x1 + radius, y1,
            x2 - radius, y1,
            x2, y1,
            x2, y1 + radius,
            x2, y2 - radius,
            x2, y2,
            x2 - radius, y2,
            x1 + radius, y2,
            x1, y2,
            x1, y2 - radius,
            x1, y1 + radius,
            x1, y1,
        ]
        canvas.create_polygon(points, smooth=True, splinesteps=32, fill=fill, outline="", tags=tag)

    def _redraw(self, event: Optional[tk.Event] = None) -> None:
        w = event.width if event else self.canvas.winfo_width()
        h = event.height if event else self.canvas.winfo_height()
        r = min(self.radius, w // 2, h // 2)
        self.canvas.config(height=h, width=w)
        self.canvas.delete("shape")
        offset = 4
        self._rounded_polygon(self.canvas, offset, offset, w - 1, h - 1, r, self.shadow_color, "shape")
        self._rounded_polygon(self.canvas, 0, 0, w - offset, h - offset, r, self.input_bg, "shape")
        # Recenter the entry vertically
        self.canvas.coords("entry", self.padding + r, h / 2)


class WeatherApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.font_family = "Poppins"
        self.colors = {
            "bg": "#050505",
            "surface": "#0d0f14",
            "shadow": "#020203",
            "accent": "#22d3ee",
            "text": "#e5e7eb",
            "muted": "#9ca3af",
            "input_bg": "#0a0c11",
        }
        self.root.title("Weather App")
        self.root.configure(padx=16, pady=16, bg=self.colors["bg"])
        self.root.resizable(width=False, height=False)
        self.icon_image = None

        header = tk.Label(
            root,
            text="Emm's Weather App",
            font=(self.font_family, 20, "bold"),
            fg=self.colors["text"],
            bg=self.colors["bg"],
        )
        header.pack(pady=(0, 12))

        form_card = RoundedCard(
            root,
            width=380,
            fg_color=self.colors["surface"],
            shadow_color=self.colors["shadow"],
            bg_color=self.colors["bg"],
            radius=18,
            padding=14,
        )
        form_card.pack(fill="x", pady=(0, 14))

        form = form_card.inner
        tk.Label(
            form,
            text="Location",
            fg=self.colors["muted"],
            bg=self.colors["surface"],
            font=(self.font_family, 11, "bold"),
        ).pack(anchor="w")
        self.location_input = RoundedEntry(
            form,
            font_family=self.font_family,
            text_color=self.colors["text"],
            bg_color=self.colors["surface"],
            input_bg=self.colors["input_bg"],
            shadow_color=self.colors["shadow"],
            radius=14,
            padding=10,
        )
        self.location_input.pack(fill="x", pady=(6, 10))
        self.location_entry = self.location_input.entry
        self.location_entry.focus()
        self.location_entry.bind("<Return>", lambda _: self.get_weather())

        tk.Button(
            form,
            text="Get Weather",
            command=self.get_weather,
            bg=self.colors["accent"],
            activebackground="#1cc4df",
            fg="#0b1324",
            activeforeground="#0b1324",
            relief="flat",
            bd=0,
            font=(self.font_family, 12, "bold"),
            padx=12,
            pady=10,
            cursor="hand2",
        ).pack(pady=(0, 6), anchor="e")

        result_card = RoundedCard(
            root,
            width=380,
            fg_color=self.colors["surface"],
            shadow_color=self.colors["shadow"],
            bg_color=self.colors["bg"],
            radius=18,
            padding=16,
        )
        result_card.pack(fill="both", expand=True)

        result_frame = result_card.inner
        self.result_var = tk.StringVar(value="Enter a location to begin.")
        self.icon_label = tk.Label(result_frame, bg=self.colors["surface"])
        self.icon_label.pack(pady=(0, 6))
        self.result_label = tk.Label(
            result_frame,
            textvariable=self.result_var,
            justify="left",
            anchor="w",
            fg=self.colors["text"],
            bg=self.colors["surface"],
            wraplength=320,
            font=(self.font_family, 12),
        )
        self.result_label.pack(fill="both", expand=True)

    def get_weather(self) -> None:
        location = self.location_entry.get().strip()
        if not location:
            messagebox.showinfo("Enter a location", "Please type a city or ZIP/postal code.")
            return
        if not API_KEY:
            self.result_var.set("Missing API key. Add your key to api_config.py (kept out of git).")
            return

        try:
            response = requests.get(
                API_URL,
                params={"key": API_KEY, "q": location, "aqi": "no"},
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as exc:
            self.result_var.set(f"Error fetching weather data: {exc}")
            self.icon_label.configure(image="")
            self.icon_image = None
            return

        self.icon_image = None
        self.icon_label.configure(image="")

        location_data = data.get("location", {})
        current = data.get("current", {})
        condition = current.get("condition", {}) or {}

        name = location_data.get("name", location)
        region = location_data.get("region", "")
        country = location_data.get("country", "")
        temp_c = current.get("temp_c", "?")
        feelslike_c = current.get("feelslike_c", "?")
        humidity = current.get("humidity", "?")
        wind_kph = current.get("wind_kph", "?")
        cond_text = condition.get("text", "Unknown")
        icon_path = condition.get("icon", "") or ""
        icon_url = f"https:{icon_path}" if icon_path.startswith("//") else icon_path
        if icon_url:
            try:
                icon_resp = requests.get(icon_url, timeout=10)
                icon_resp.raise_for_status()
                icon_b64 = base64.b64encode(icon_resp.content).decode("ascii")
                self.icon_image = tk.PhotoImage(data=icon_b64)
                self.icon_label.configure(image=self.icon_image, bg=self.colors["surface"])
            except requests.RequestException:
                self.icon_image = None
                self.icon_label.configure(image="")

        location_line = ", ".join(filter(None, [name, region, country]))
        details = [
            location_line or location,
            f"Condition: {cond_text}",
            f"Temperature: {temp_c}°C (feels like {feelslike_c}°C)",
            f"Humidity: {humidity}%",
            f"Wind: {wind_kph} kph",
        ]
        self.result_var.set("\n".join(details))


def main() -> None:
    root = tk.Tk()
    WeatherApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
