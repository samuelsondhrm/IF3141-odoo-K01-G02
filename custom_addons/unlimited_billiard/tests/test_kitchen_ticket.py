import base64
import json

from odoo.tests import HttpCase, tagged


@tagged("post_install", "-at_install")
class TestKitchenTicket(HttpCase):
    def test_tiket_tersimpan_sebagai_gambar(self):
        rina = self.env.ref("unlimited_billiard.user_rina")
        rina.password = "rina-uji-123"
        self.authenticate("rina.admin", "rina-uji-123")
        img = base64.b64encode(bytes.fromhex("ffd8ffe000104a46494600010100000100010000ffd9")).decode()
        res = self.url_open(
            "/hw_proxy/default_printer_action",
            data=json.dumps({"jsonrpc": "2.0", "method": "call",
                             "params": {"data": {"action": "print_receipt", "receipt": img}}}),
            headers={"Content-Type": "application/json"},
        )
        self.assertTrue(res.json().get("result"))
        tiket = self.env["ir.attachment"].search([("res_model", "=", "pos.printer")])
        self.assertEqual(len(tiket), 1)
        self.assertEqual(tiket.mimetype, "image/jpeg")
