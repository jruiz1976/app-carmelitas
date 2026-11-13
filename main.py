import os
import sqlite3
from datetime import datetime
import flet as ft

BASE_DIR = os.getenv("FLET_APP_STORAGE_DATA", os.getcwd())
DB_NAME = os.path.join(BASE_DIR, "sistema_carmelitas.db")

MESES = {
    "01": "Enero", "02": "Febrero", "03": "Marzo", "04": "Abril",
    "05": "Mayo", "06": "Junio", "07": "Julio", "08": "Agosto",
    "09": "Septiembre", "10": "Octubre", "11": "Noviembre", "12": "Diciembre"
}

TEMAS = {
    "Carmelita Clásico": {"bg": "#f5efe6", "header": "#5d4037", "btn": "#6d4c41", "dark": False},
    "Azul Institucional": {"bg": "#f0f4f8", "header": "#1976d2", "btn": "#2196f3", "dark": False},
    "Verde Esperanza": {"bg": "#e8f5e9", "header": "#2e7d32", "btn": "#388e3c", "dark": False},
    "Vino Formal": {"bg": "#fce4ec", "header": "#880e4f", "btn": "#ad1457", "dark": False},
    "Modo Oscuro": {"bg": "#121212", "header": "#1f1f1f", "btn": "#00897b", "dark": True}
}

CATEGORIAS = [
    "Diezmo",
    "Ofrenda",
    "Servicios Públicos",
    "Ayuda Social",
    "Mantenimiento",
    "Otros"
]


def inicializar_base_datos():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS movimientos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id TEXT,
                fecha TEXT,
                tipo TEXT,
                categoria TEXT,
                descripcion TEXT,
                monto REAL
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS cfg (
                id INT PRIMARY KEY,
                sede TEXT,
                enc TEXT,
                ced TEXT
            )
        """)
        c.execute("""
            INSERT OR IGNORE INTO cfg
            VALUES (1, 'Comunidad Carmelitas Centro', 'Hna. Yerica Blanco', 'V-12.345.678')
        """)
        conn.commit()


def formatear_moneda(valor):
    return f"{float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def main(page: ft.Page):
    inicializar_base_datos()
    uid = "carmelitas1"
    tema_actual = {"data": TEMAS["Carmelita Clásico"]}

    page.title = "Contabilidad Carmelitas"
    page.padding = 0

    def obtener_config():
        with sqlite3.connect(DB_NAME) as conn:
            fila = conn.cursor().execute("SELECT sede, enc, ced FROM cfg WHERE id=1").fetchone()
        return fila or ("Comunidad Carmelitas Centro", "Hna. Yerica Blanco", "V-12.345.678")

    def mostrar_mensaje(texto, color="green"):
        page.overlay = [ctrl for ctrl in page.overlay if not isinstance(ctrl, ft.SnackBar)]
        sb = ft.SnackBar(ft.Text(texto, color="white"), bgcolor=color)
        page.overlay.append(sb)
        sb.open = True
        page.update()

    def abrir_dialogo(dlg):
        page.overlay = [ctrl for ctrl in page.overlay if not isinstance(ctrl, ft.AlertDialog)]
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    sede_ini, enc_ini, ced_ini = obtener_config()

    # Controles principales
    lbl_sede = ft.Text(
        sede_ini.upper(),
        color="white70",
        size=10,
        weight=ft.FontWeight.BOLD,
        max_lines=1,
        overflow=ft.TextOverflow.ELLIPSIS
    )
    lbl_saldo = ft.Text("Bs. 0,00", size=18, weight=ft.FontWeight.BOLD, color="white")
    lista = ft.ListView(expand=True, spacing=8, padding=10)

    # Filtros de movimientos
    txt_fec = ft.TextField(label="Filtrar fecha", dense=True, expand=True, on_change=lambda e: cargar_movimientos())
    dd_fcat = ft.Dropdown(
        label="Categoría",
        dense=True,
        width=135,
        value="Todas",
        options=[ft.dropdown.Option("Todas")] + [ft.dropdown.Option(c) for c in CATEGORIAS],
        on_select=lambda e: cargar_movimientos()
    )

    # Formulario de registro
    dd_tipo = ft.Dropdown(
        label="Tipo",
        value="Ingreso",
        options=[ft.dropdown.Option("Ingreso"), ft.dropdown.Option("Egreso")]
    )
    dd_cat = ft.Dropdown(
        label="Categoría",
        value="Ofrenda",
        options=[ft.dropdown.Option(c) for c in CATEGORIAS]
    )
    txt_monto = ft.TextField(label="Monto (Bs.)", keyboard_type=ft.KeyboardType.NUMBER)
    txt_desc = ft.TextField(label="Descripción (Opcional)", multiline=True, min_lines=2, max_lines=3)

    # Configuración
    dd_tema = ft.Dropdown(
        label="Tema Visual (Paleta de Colores)",
        value="Carmelita Clásico",
        options=[ft.dropdown.Option(t) for t in TEMAS],
        on_select=lambda e: aplicar_tema(e.control.value)
    )
    t_sede = ft.TextField(label="Comunidad / Sede", value=sede_ini, dense=True)
    t_enc = ft.TextField(label="Hermana Responsable", value=enc_ini, dense=True)
    t_ced = ft.TextField(label="Cédula", value=ced_ini, dense=True)

    def guardar_config(e):
        sede_val = t_sede.value.strip() or "Comunidad Carmelitas Centro"
        enc_val = t_enc.value.strip()
        ced_val = t_ced.value.strip()
        with sqlite3.connect(DB_NAME) as conn:
            conn.cursor().execute(
                "UPDATE cfg SET sede=?, enc=?, ced=? WHERE id=1",
                (sede_val, enc_val, ced_val)
            )
            conn.commit()
        lbl_sede.value = sede_val.upper()
        mostrar_mensaje("Configuración guardada")

    def borrar_movimiento(mov_id):
        with sqlite3.connect(DB_NAME) as conn:
            conn.cursor().execute("DELETE FROM movimientos WHERE id = ?", (mov_id,))
            conn.commit()
        cargar_movimientos()
        mostrar_mensaje("Movimiento eliminado", "red")

    def ver_recibo(sede, fec, cat, desc, mon):
        color_hdr = tema_actual["data"]["header"]

        def cerrar(e):
            dlg.open = False
            page.update()

        dlg = ft.AlertDialog(
            title=ft.Text("COMPROBANTE DE PAGO", weight=ft.FontWeight.BOLD, size=15, color=color_hdr),
            content=ft.Column(
                tight=True,
                spacing=6,
                controls=[
                    ft.Text(sede.upper(), size=10, color="grey"),
                    ft.Container(
                        padding=10,
                        bgcolor="#f5efe6" if not tema_actual["data"]["dark"] else "#2c2c2c",
                        border_radius=8,
                        content=ft.Text(
                            f"Bs. {formatear_moneda(mon)}",
                            size=18,
                            weight=ft.FontWeight.BOLD,
                            color="#c62828"
                        )
                    ),
                    ft.Text(f"Fecha: {fec}", size=12),
                    ft.Text(f"Concepto: {cat}", size=12),
                    ft.Text(f"Detalle: {desc or 'Sin detalle'}", size=12),
                    ft.Divider(),
                    ft.Text("Firma: Entregado / Recibido Conforme", size=11, italic=True, color="grey")
                ]
            ),
            actions=[ft.Button("Cerrar", bgcolor=color_hdr, color="white", on_click=cerrar)]
        )
        abrir_dialogo(dlg)

    def ver_reporte(e):
        sede, enc, ced = obtener_config()
        color_hdr = tema_actual["data"]["header"]

        with sqlite3.connect(DB_NAME) as conn:
            filas = conn.cursor().execute(
                "SELECT fecha, tipo, categoria, monto FROM movimientos WHERE usuario_id = ? ORDER BY id DESC",
                (uid,)
            ).fetchall()

        ing = sum(float(m) for _, t, _, m in filas if t == "Ingreso")
        egr = sum(float(m) for _, t, _, m in filas if t == "Egreso")
        saldo = ing - egr

        items = [
            ft.Text(sede.upper(), size=11, weight=ft.FontWeight.BOLD, color=color_hdr),
            ft.Text(f"Emitido: {datetime.now().strftime('%d/%m/%Y %H:%M')}", size=10, color="grey"),
            ft.Divider()
        ]

        for fec, tip, cat, mon in filas:
            es_ing = tip == "Ingreso"
            items.append(
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text(f"{cat} ({fec[:5]})", size=11, expand=True, overflow=ft.TextOverflow.ELLIPSIS),
                        ft.Text(
                            f"{'+' if es_ing else '-'}Bs. {formatear_moneda(mon)}",
                            size=11,
                            weight=ft.FontWeight.BOLD,
                            color="#2e7d32" if es_ing else "#c62828"
                        )
                    ]
                )
            )

        items.extend([
            ft.Divider(),
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Text("SALDO EN CAJA:", weight=ft.FontWeight.BOLD, size=12),
                    ft.Text(
                        f"Bs. {formatear_moneda(saldo)}",
                        weight=ft.FontWeight.BOLD,
                        size=13,
                        color="#2e7d32" if saldo >= 0 else "#c62828"
                    )
                ]
            ),
            ft.Divider(),
            ft.Text(f"Firma: {enc}", size=11, weight=ft.FontWeight.BOLD, color=color_hdr),
            ft.Text(f"Responsable Control Diario - C.I.: {ced}", size=10, color="grey")
        ])

        def cerrar(ev):
            dlg.open = False
            page.update()

        dlg = ft.AlertDialog(
            title=ft.Text("REPORTE CONTABLE OFICIAL", size=14, weight=ft.FontWeight.BOLD),
            content=ft.Column(scroll=ft.ScrollMode.AUTO, tight=True, spacing=6, controls=items),
            actions=[ft.Button("Cerrar", bgcolor=color_hdr, color="white", on_click=cerrar)]
        )
        abrir_dialogo(dlg)

    def construir_tarjeta(mov_id, fec, tip, cat, desc, mon):
        es_ing = tip == "Ingreso"
        col = "#2e7d32" if es_ing else "#c62828"
        return ft.Card(
            key=str(mov_id),
            content=ft.Container(
                padding=10,
                content=ft.Row(
