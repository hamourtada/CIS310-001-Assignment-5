import tkinter as tk
from tkinter import ttk, messagebox
import asyncio
import threading
from bleak import BleakScanner, BleakClient

# Create a dedicated asyncio event loop for BLE
class BLETaskThread(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.loop = asyncio.new_event_loop()

    def run(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def stop(self):
        self.loop.call_soon_threadsafe(self.loop.stop)

ble_task_thread = BLETaskThread()
ble_task_thread.start()

# Run asyncio tasks in the BLE event loop
def run_async_task(coro):
    asyncio.run_coroutine_threadsafe(coro, ble_task_thread.loop)

class TemperatureMonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("BLE Temperature Monitor")

        # UI Components
        frame = ttk.Frame(root, padding="10")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.connect_button = ttk.Button(frame, text="Connect to BLE-TEMP", command=self.connect_device)
        self.connect_button.grid(row=0, column=0, padx=5, pady=5)
        
        self.disconnect_button = ttk.Button(frame, text="Disconnect", command=self.disconnect_device, state="disabled")
        self.disconnect_button.grid(row=0, column=1, padx=5, pady=5)

        # Temperature display labels
        self.temp_c_label = ttk.Label(frame, text="Temperature (°C): --", font=("Arial", 16))
        self.temp_c_label.grid(row=1, column=0, columnspan=2, pady=5)

        self.temp_f_label = ttk.Label(frame, text="Temperature (°F): --", font=("Arial", 16))
        self.temp_f_label.grid(row=2, column=0, columnspan=2, pady=5)

        # Thermometer display
        self.canvas = tk.Canvas(frame, width=200, height=400, bg="white")
        self.canvas.grid(row=3, column=0, columnspan=2, pady=10)
        self.draw_thermometer()

        # BLE-related variables
        self.client = None
        self.temperature_uuid = "00000001-5EC4-4083-81CD-A10B8D5CF6EC"  # Replace with your BLE temperature UUID
        self.temperature = 0

        # Handle application close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def draw_thermometer(self):
        # Thermometer outline
        self.canvas.create_rectangle(75, 50, 125, 350, outline="black", width=2)
        self.canvas.create_oval(50, 350, 150, 450, outline="black", width=2)
        # Initial thermometer level
        self.thermometer_level = self.canvas.create_rectangle(76, 350, 124, 350, fill="red", outline="red")

        # Add scale numbers to the thermometer
        for i in range(0, 51, 10):
            y = 350 - (300 * i / 50)
            self.canvas.create_text(60, y, text=f"{i}°C", font=("Arial", 10), anchor="e")
            temp_f = (i * 9 / 5) + 32
            self.canvas.create_text(140, y, text=f"{int(temp_f)}°F", font=("Arial", 10), anchor="w")

    def update_thermometer(self, temperature):
        # Map temperature to height (assume 0°C to 50°C range)
        min_temp, max_temp = 0, 50
        min_y, max_y = 350, 50
        level = max_y + (min_y - max_y) * (temperature - min_temp) / (max_temp - min_temp)
        level = max(min(level, min_y), max_y)  # Clamp value within bounds

        self.canvas.coords(self.thermometer_level, 76, level, 124, 350)

    def update_temperature_labels(self, temperature):
        temp_c = temperature
        temp_f = (temperature * 9 / 5) + 32
        self.temp_c_label.config(text=f"Temperature (°C): {temp_c:.2f}")
        self.temp_f_label.config(text=f"Temperature (°F): {temp_f:.2f}")

    async def ble_connect(self):
        try:
            # Search for the BLE-TEMP device
            devices = await BleakScanner.discover()
            device = next((d for d in devices if d.name == "BLE-TEMP"), None)

            if device is None:
                raise Exception("BLE-TEMP device not found.")

            # Connect to the device
            self.client = BleakClient(device.address)
            await self.client.connect()
            self.connect_button.config(state="disabled")
            self.disconnect_button.config(state="normal")
            messagebox.showinfo("Connection", f"Successfully connected to {device.name}!")
            await self.start_notifications()
        except Exception as e:
            messagebox.showerror("Connection Error", str(e))

    def connect_device(self):
        run_async_task(self.ble_connect())

    async def start_notifications(self):
        if self.client and self.client.is_connected:
            await self.client.start_notify(self.temperature_uuid, self.handle_temperature)

    def handle_temperature(self, sender, data):
        try:
            temperature_str = data.decode("utf-8").strip()
            self.temperature = float(temperature_str)
            self.update_thermometer(self.temperature)
            self.update_temperature_labels(self.temperature)
        except Exception as e:
            print(f"Error parsing temperature: {e}")

    async def ble_disconnect(self):
        if self.client:
            await self.client.disconnect()
            self.client = None
            self.connect_button.config(state="normal")
            self.disconnect_button.config(state="disabled")
            self.temperature = 0
            self.update_thermometer(self.temperature)
            self.update_temperature_labels(0)
            messagebox.showinfo("Disconnection", "Disconnected from BLE-TEMP.")

    def disconnect_device(self):
        run_async_task(self.ble_disconnect())

    def on_closing(self):
        ble_task_thread.stop()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = TemperatureMonitorApp(root)
    root.mainloop()
