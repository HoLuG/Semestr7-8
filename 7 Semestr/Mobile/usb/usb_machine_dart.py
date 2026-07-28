import time
import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

import usb
import usb.core
import usb.util
from usb.core import Device, Endpoint

import typer
from rich.console import Console

class AppMode(Enum):
    Write = "write"
    Read = "read"


@dataclass
class App:
    device: Optional[Device] = None
    console: Console = field(default_factory=Console)

    def select_device(self):
        lst: list[usb.Device] = list(usb.core.find(find_all=True))

        if not lst:
            self.console.print("[bold blue]Waiting for devices...")
            while not lst:
                lst = list(usb.core.find(find_all=True))
                time.sleep(1)

        self.console.print("[bold blue]Available devices:")
        for i, dev in enumerate(lst):
            vid = hex(dev.idVendor)
            pid = hex(dev.idProduct)

            try:
                manufacturer = usb.util.get_string(dev, dev.iManufacturer)
            except Exception:
                manufacturer = None

            try:
                product = usb.util.get_string(dev, dev.iProduct)
            except Exception:
                product = None

            self.console.print(
                f"[bold green][{i}] "
                f"VID={vid} PID={pid} "
                f"Manufacturer={manufacturer} Product={product}"
            )

        ind = int(self.console.input("[bold blue]Select device index: "))
        self.device = lst[ind]

    def prepare_device(self):
        for command_name, command in [
            ("Verifying protocol", self.set_protocol),
            ("Sending accessory parameters", self.send_accessory_parameters),
            ("Triggering accessory mode", self.set_accessory_mode),
        ]:
            self.console.print(f"{command_name}.........", end="")
            try:
                command()
            except Exception:
                self.console.print("[bold red]FAIL")
                self.console.print_exception()
                sys.exit(1)
            else:
                self.console.print("[bold green]OK")

    def set_protocol(self):
        try:
            self.device.set_configuration()
        except usb.core.USBError as e:
            # 16 == already configured
            if e.errno != 16:
                raise

        ret = self.device.ctrl_transfer(0xC0, 51, 0, 0, 2)
        protocol = ret[0]

        if protocol < 2:
            raise ValueError(f"Protocol version {protocol} < 2 is not supported")

    def send_accessory_parameters(self):
        def send_string(str_id: int, value: str):
            ret = self.device.ctrl_transfer(0x40, 52, 0, str_id, value, 0)
            if ret != len(value):
                raise ValueError("Received non-valid response")

        send_string(0, "dvpashkevich")
        send_string(1, "PyAndroidCompanion")
        send_string(2, "A Python based Android accessory companion")
        send_string(3, "0.1.0")

    def _reconnect_accessory_device(self):
        ANDROID_VID = 0x18D1
        self.console.print("[bold blue]Reconnecting to accessory device...")

        dev = None
        for _ in range(10):
            candidates = [
                d for d in usb.core.find(find_all=True)
                if d.idVendor == ANDROID_VID
            ]
            if candidates:
                dev = candidates[0]
                break
            time.sleep(0.5)

        if not dev:
            raise ValueError(
                "Accessory device not found after switching mode.\n"
                "Проверь, что телефон действительно перешёл в accessory mode."
            )

        try:
            dev.set_configuration()
        except usb.core.USBError as e:
            if e.errno != 16:
                raise

        try:
            manufacturer = usb.util.get_string(dev, dev.iManufacturer)
        except Exception:
            manufacturer = None

        try:
            product = usb.util.get_string(dev, dev.iProduct)
        except Exception:
            product = None

        self.console.print(
            f"[bold blue]Reconnected to "
            f"VID={hex(dev.idVendor)} "
            f"PID={hex(dev.idProduct)} "
            f"Manufacturer={manufacturer} "
            f"Product={product}"
        )

        self.device = dev

    def set_accessory_mode(self):
        ret = self.device.ctrl_transfer(0x40, 53, 0, 0, None, 0)
        if ret:
            raise ValueError("Failed to trigger accessory mode")

        time.sleep(1)
        self._reconnect_accessory_device()

    def _ensure_configured(self):
        try:
            self.device.set_configuration()
        except usb.core.USBError as e:
            if e.errno != 16:
                raise

    def accept_data(self):
        self.console.print("[bold blue]Accepting data from Android device...")
        self._ensure_configured()

        cfg = self.device.get_active_configuration()
        intf = cfg[(0, 0)]

        try:
            usb.util.claim_interface(self.device, intf.bInterfaceNumber)
        except usb.core.USBError:
            pass

        ep_in: Endpoint = usb.util.find_descriptor(
            intf,
            custom_match=lambda e: usb.util.endpoint_direction(
                e.bEndpointAddress
            ) == usb.util.ENDPOINT_IN,
        )

        while True:
            try:
                data = ep_in.read(1024, timeout=0)
                message = bytes(data).decode(errors="ignore")
                if message.strip():
                    self.console.print(f"[green]Android: {message}", end="")
            except usb.core.USBError as e:
                self.console.print(f"[red]Failed to receive data: {e}")
                break
            except KeyboardInterrupt:
                self.console.print("\n[bold yellow]Disconnecting device...")
                try:
                    self.device.detach_kernel_driver(0)
                except (NotImplementedError, usb.core.USBError):
                    pass
                break

    def write(self):
        self._ensure_configured()

        cfg = self.device.get_active_configuration()
        intf = cfg[(0, 0)]

        try:
            usb.util.claim_interface(self.device, intf.bInterfaceNumber)
        except usb.core.USBError:
            pass

        ep_out: Endpoint = usb.util.find_descriptor(
            intf,
            custom_match=lambda e: usb.util.endpoint_direction(
                e.bEndpointAddress
            ) == usb.util.ENDPOINT_OUT,
        )

        while True:
            message = self.console.input("[bold blue]Write: ")
            data = (message + "\n").encode("utf-8")

            try:
                written = ep_out.write(data, timeout=5000)
                self.console.print(f"[green]Sent {written} bytes")
            except usb.core.USBTimeoutError as e:
                self.console.print(f"[red]USB write timeout: {e}")
            except usb.core.USBError as e:
                self.console.print(f"[red]USB write error: {e}")
                break


def main(mode: AppMode = AppMode.Read):
    app = App()
    app.select_device()

    if not (
        app.device.idVendor == 0x18D1
        and 0x2D00 <= app.device.idProduct <= 0x2D05
    ):
        app.prepare_device()

    if mode == AppMode.Write:
        app.write()
    else:
        app.accept_data()


if __name__ == "__main__":
    typer.run(main)
