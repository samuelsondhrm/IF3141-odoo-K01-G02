from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare

# Nilai status mengikuti baseline M4 (Tabel 2.4): MenungguKonfirmasi, Terkonfirmasi, Keberatan.
STATUS = [
    ("menunggu_konfirmasi", "Menunggu Konfirmasi"),
    ("terkonfirmasi", "Terkonfirmasi"),
    ("keberatan", "Keberatan"),
]


class SerahTerimaShift(models.Model):
    """D-19 SerahTerimaShift / K-15 (FR-05)."""

    _name = "ub.serah.terima.shift"
    _description = "Serah Terima Shift Kitchen"
    _inherit = ["mail.thread"]
    _order = "waktu desc"

    waktu = fields.Datetime(required=True, default=fields.Datetime.now, readonly=True)
    penyerah_id = fields.Many2one(
        "res.users", string="Penyerah", required=True, default=lambda self: self.env.user, readonly=True
    )
    penerima_id = fields.Many2one("res.users", string="Penerima", required=True, tracking=True)
    status = fields.Selection(STATUS, default="menunggu_konfirmasi", required=True, readonly=True, tracking=True)
    catatan = fields.Text()
    keberatan = fields.Text()
    detail_ids = fields.One2many("ub.detail.serah.terima", "serah_terima_id", string="Bahan Kritis")

    @api.depends("waktu", "penyerah_id")
    def _compute_display_name(self):
        for rec in self:
            waktu = fields.Datetime.context_timestamp(rec, rec.waktu).strftime("%d/%m/%Y %H:%M") if rec.waktu else ""
            rec.display_name = _("Serah Terima %(waktu)s", waktu=waktu)

    @api.constrains("penyerah_id", "penerima_id")
    def _check_beda_orang(self):
        if any(rec.penyerah_id == rec.penerima_id for rec in self):
            raise ValidationError(_("Penyerah dan penerima shift harus orang yang berbeda."))

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records.filtered(lambda r: not r.detail_ids).action_bandingkan_stok()
        return records

    def _cek_bisa_diproses(self):
        for rec in self:
            if rec.status != "menunggu_konfirmasi":
                raise UserError(_("Serah terima ini sudah diproses."))
            if rec.penerima_id != self.env.user:
                raise UserError(_("Hanya penerima shift (%s) yang boleh memproses.", rec.penerima_id.name))

    def action_bandingkan_stok(self):
        """bandingkanStok(): isi/segarkan stok sistem semua bahan bertag Bahan Kritis."""
        tag = self.env.ref("unlimited_billiard.tag_bahan_kritis")
        bahan = self.env["product.product"].search([("product_tag_ids", "in", tag.ids)], order="name")
        for rec in self:
            if rec.status != "menunggu_konfirmasi":
                raise UserError(_("Serah terima ini sudah diproses."))
            existing = {d.bahan_id: d for d in rec.detail_ids}
            for product in bahan:
                if product in existing:
                    existing[product].stok_sistem = product.qty_available
                else:
                    # Hitung cepat diisi awal = stok sistem; penyerah cukup mengubah yang berbeda.
                    rec.detail_ids = [fields.Command.create({
                        "bahan_id": product.id,
                        "stok_sistem": product.qty_available,
                        "hitung_cepat": product.qty_available,
                    })]

    def action_konfirmasi(self):
        """konfirmasi(): penerima menyetujui hasil hitung cepat."""
        self._cek_bisa_diproses()
        self.status = "terkonfirmasi"

    def action_catat_keberatan(self):
        """catatKeberatan(): penerima menolak hasil hitung cepat dengan alasan."""
        self._cek_bisa_diproses()
        if any(not rec.keberatan for rec in self):
            raise UserError(_("Isi kolom Keberatan terlebih dahulu."))
        self.status = "keberatan"


class DetailSerahTerima(models.Model):
    """D-20 DetailSerahTerima."""

    _name = "ub.detail.serah.terima"
    _description = "Detail Serah Terima Shift"

    serah_terima_id = fields.Many2one("ub.serah.terima.shift", required=True, ondelete="cascade")
    bahan_id = fields.Many2one("product.product", string="Bahan", required=True)
    uom_id = fields.Many2one(related="bahan_id.uom_id")
    stok_sistem = fields.Float(digits="Product Unit of Measure", readonly=True)
    hitung_cepat = fields.Float(digits="Product Unit of Measure")
    kondisi = fields.Char()
    is_berbeda = fields.Boolean(string="Berbeda", compute="_compute_is_berbeda", store=True)

    _sql_constraints = [
        ("bahan_unik", "unique(serah_terima_id, bahan_id)", "Bahan sudah ada di serah terima ini."),
    ]

    @api.depends("hitung_cepat", "stok_sistem", "bahan_id.uom_id.rounding")
    def _compute_is_berbeda(self):
        for line in self:
            rounding = line.bahan_id.uom_id.rounding or 0.01
            line.is_berbeda = float_compare(line.hitung_cepat, line.stok_sistem, precision_rounding=rounding) != 0
