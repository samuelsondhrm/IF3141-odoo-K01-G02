{
    "name": "Unlimited Billiard & Cafe",
    "summary": "Konfigurasi, data dummy M4, dan serah terima shift Kitchen (L-17)",
    "version": "17.0.1.0.0",
    "license": "LGPL-3",
    "author": "IF3141 K01-G02",
    "category": "Point of Sale",
    "depends": [
        "contacts",
        "l10n_id",
        "point_of_sale",
        "pos_restaurant",
        "pos_loyalty",
        "pos_mrp",
        "purchase_stock",
    ],
    "application": True,
    # Urutan penting: perusahaan + akun dulu (POS butuh chart of accounts), lalu data induk.
    "data": [
        "security/ir.model.access.csv",
        "views/serah_terima_views.xml",
        "data/company.xml",
        "data/master_data.xml",
        "data/pos_data.xml",
        "data/users_partners.xml",
    ],
}
