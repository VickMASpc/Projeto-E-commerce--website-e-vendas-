import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk

import config
import database
from api.server import start_api_server
from ui.coupons_view import CouponsView
from ui.dashboard_view import DashboardView
from ui.orders_view import OrdersView
from ui.products_view import ProductsInventoryView
from ui.settings_view import SettingsView
from ui.shell import build_tabview, configure_treeview_style

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class SistemaLogisticaApp:
    def __init__(self, root):
        self.root = root
        self.root.title(config.APP_NAME)
        self.root.geometry("1120x760")

        configure_treeview_style()
        self.notebook, tabs = build_tabview(self.root)

        self.dashboard_view = DashboardView(
            tab=tabs["dashboard"],
            refresh_callback=self._refresh_all,
        )
        self.products_view = ProductsInventoryView(
            root=self.root,
            tab=tabs["products"],
            refresh_callback=self._refresh_all,
        )
        self.orders_view = OrdersView(
            root=self.root,
            tab=tabs["orders"],
            refresh_callback=self._refresh_all,
        )
        self.coupons_view = CouponsView(
            root=self.root,
            tab=tabs["coupons"],
            refresh_callback=self._refresh_all,
        )
        self.settings_view = SettingsView(
            tab=tabs["settings"],
            refresh_callback=self._refresh_all,
        )

        self.dashboard_view.build()
        self.products_view.build()
        self.orders_view.build()
        self.coupons_view.build()
        self.settings_view.build()
        self._refresh_all()
        self._start_api_server()

        if database.USE_FIREBASE:
            database.listen_to_orders(
                lambda: self.root.after(0, self._refresh_realtime)
            )

    def _refresh_realtime(self):
        self._refresh_all()

    def _refresh_all(self):
        self.products_view.load_products()
        self.orders_view.load_orders()
        self.coupons_view.load_coupons()
        self.dashboard_view.refresh()
        self.settings_view.refresh()

    def _start_api_server(self):
        def _on_order_created(order_id: str, customer_name: str) -> None:
            self.root.after(0, self._refresh_all)
            self.root.after(
                0,
                lambda: messagebox.showinfo(
                    "Novo pedido",
                    f"Um novo pedido de {customer_name} foi recebido.",
                ),
            )

        start_api_server(
            host=config.API_HOST,
            port=config.API_PORT,
            on_order_created=_on_order_created,
        )


if __name__ == "__main__":
    root = ctk.CTk()
    app = SistemaLogisticaApp(root)
    root.mainloop()
