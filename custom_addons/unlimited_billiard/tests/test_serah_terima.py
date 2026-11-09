from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase


class TestSerahTerima(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ujang = cls.env.ref("unlimited_billiard.user_ujang")
        cls.fajar = cls.env.ref("unlimited_billiard.user_fajar")
        cls.Serah = cls.env["ub.serah.terima.shift"]

    def _buat(self):
        return self.Serah.with_user(self.ujang).create({"penerima_id": self.fajar.id})

    def test_isi_bahan_kritis_dan_selisih(self):
        rec = self._buat()
        # 7 bahan bertag Bahan Kritis, stok sistem = stok awal data dummy
        self.assertEqual(len(rec.detail_ids), 7)
        ayam = rec.detail_ids.filtered(lambda d: d.bahan_id == self.env.ref("unlimited_billiard.b04"))
        self.assertEqual(ayam.stok_sistem, 6)
        self.assertFalse(ayam.is_berbeda)
        ayam.hitung_cepat = 5.9
        self.assertTrue(ayam.is_berbeda)

    def test_konfirmasi_hanya_oleh_penerima(self):
        rec = self._buat()
        with self.assertRaises(UserError):
            rec.with_user(self.ujang).action_konfirmasi()
        rec.with_user(self.fajar).action_konfirmasi()
        self.assertEqual(rec.status, "terkonfirmasi")
        with self.assertRaises(UserError):
            rec.with_user(self.fajar).action_konfirmasi()

    def test_keberatan_wajib_alasan(self):
        rec = self._buat().with_user(self.fajar)
        with self.assertRaises(UserError):
            rec.action_catat_keberatan()
        rec.keberatan = "Ayam fillet kurang 0,1 kg"
        rec.action_catat_keberatan()
        self.assertEqual(rec.status, "keberatan")

    def test_penyerah_bukan_penerima(self):
        with self.assertRaises(ValidationError):
            self.Serah.with_user(self.ujang).create({"penerima_id": self.ujang.id})
