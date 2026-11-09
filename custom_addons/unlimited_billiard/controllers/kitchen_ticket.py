from odoo import http
from odoo.http import request


class KitchenTicketProxy(http.Controller):
    # shortcut: meniru endpoint IoT Box supaya tiket Kitchen (L-10) tersimpan sebagai gambar,
    # bukan dicetak; ganti dengan printer ePOS/IoT sungguhan bila perangkatnya ada.
    @http.route("/hw_proxy/default_printer_action", type="json", auth="user")
    def default_printer_action(self, data, **kw):
        receipt = data.get("receipt") if isinstance(data, dict) else None
        if data.get("action") == "print_receipt" and isinstance(receipt, str):
            printer = request.env.ref("unlimited_billiard.printer_kitchen")
            request.env["ir.attachment"].sudo().create({
                "name": "Tiket Kitchen.jpg",
                "datas": receipt,
                "mimetype": "image/jpeg",
                "res_model": "pos.printer",
                "res_id": printer.id,
            })
        return True
