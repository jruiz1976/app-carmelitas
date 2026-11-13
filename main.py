import sqlite3
import os
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

def inicializar_base_datos():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS movimientos (id INTEGER PRIMARY KEY AUTOINCREMENT, usuario_id TEXT, fecha TEXT, tipo TEXT, categoria TEXT, descripcion TEXT, monto REAL)")
    c.execute("CREATE TABLE IF NOT EXISTS cfg (id INT PRIMARY KEY, sede TEXT, enc TEXT, ced TEXT)")
    c.execute("INSERT OR IGNORE INTO cfg VALUES (1, 'Comunidad Carmelitas Centro', 'Hna. Yerica Blanco', 'V-12.345.678')")
    conn.commit()
    conn.close()

def formatear_moneda(v):
    return f"{float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def main(page: ft.Page):
    inicializar_base_datos()
    uid = "carmelitas1"
    cats = ["Diezmo", "Ofrenda", "Servicios Públicos", "Ayuda Social", "Mantenimiento", "Otros"]
    page.title = "Contabilidad Carmelitas"
    page.padding = 0

    def gcfg():
        cn = sqlite3.connect(DB_NAME)
        r = cn.cursor().execute("SELECT sede, enc, ced FROM cfg WHERE id=1").fetchone()
        cn.close()
        return r or ("Comunidad Carmelitas Centro", "Hna. Yerica Blanco", "V-12.345.678")

    def msg(t, col="green"):
        sb = ft.SnackBar(ft.Text(t, color="white"), bgcolor=col)
        page.overlay.append(sb)
        sb.open = True
        page.update()

    s0, e0, c0 = gcfg()
    lbl_sede = ft.Text(s0.upper(), color="white70", size=10, weight=ft.FontWeight.BOLD, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS)
    lbl_saldo = ft.Text("Bs. 0,00", size=18, weight=ft.FontWeight.BOLD, color="white")
    lista = ft.ListView(expand=True, spacing=8, padding=10)
    txt_fec = ft.TextField(label="Filtrar fecha", dense=True, expand=True, on_change=lambda e: cargar())
    dd_fcat = ft.Dropdown(label="Categoría", dense=True, width=135, value="Todas", options=[ft.dropdown.Option("Todas")] + [ft.dropdown.Option(c) for c in cats], on_select=lambda e: cargar())
    dd_tipo = ft.Dropdown(label="Tipo", value="Ingreso", options=[ft.dropdown.Option("Ingreso"), ft.dropdown.Option("Egreso")])
    dd_cat = ft.Dropdown(label="Categoría", value="Ofrenda", options=[ft.dropdown.Option(c) for c in cats])
    txt_monto = ft.TextField(label="Monto (Bs.)", keyboard_type=ft.KeyboardType.NUMBER)
    txt_desc = ft.TextField(label="Descripción (Opcional)", multiline=True, min_lines=2, max_lines=3)
    dd_tema = ft.Dropdown(label="Tema Visual (Paleta de Colores)", value="Carmelita Clásico", options=[ft.dropdown.Option(t) for t in TEMAS], on_select=lambda e: tema(e.control.value))
    t_s = ft.TextField(label="Comunidad / Sede", value=s0, dense=True)
    t_e = ft.TextField(label="Hermana Responsable", value=e0, dense=True)
    t_c = ft.TextField(label="Cédula", value=c0, dense=True)

    def scfg(e):
        cn = sqlite3.connect(DB_NAME)
        cn.cursor().execute("UPDATE cfg SET sede=?, enc=?, ced=? WHERE id=1", (t_s.value.strip(), t_e.value.strip(), t_c.value.strip()))
        cn.commit()
        cn.close()
        lbl_sede.value = t_s.value.strip().upper()
        msg("Configuración guardada")
        page.update()

    def borrar(mid):
        conn = sqlite3.connect(DB_NAME)
        conn.cursor().execute("DELETE FROM movimientos WHERE id = ?", (mid,))
        conn.commit()
        conn.close()
        cargar()
        msg("Movimiento eliminado", "red")
    def ver_recibo(sede, fec, cat, desc, mon):
        def cerrar(e):
            dlg.open = False
            page.update()
        dlg = ft.AlertDialog(
            title=ft.Text("COMPROBANTE DE PAGO", weight=ft.FontWeight.BOLD, size=15, color="#5d4037"),
            content=ft.Column(tight=True, spacing=6, controls=[
                ft.Text(sede.upper(), size=10, color="grey"),
                ft.Container(padding=10, bgcolor="#f5efe6", border_radius=8, content=ft.Text(f"Bs. {formatear_moneda(mon)}", size=18, weight=ft.FontWeight.BOLD, color="#c62828")),
                ft.Text(f"Fecha: {fec}", size=12),
                ft.Text(f"Concepto: {cat}", size=12),
                ft.Text(f"Detalle: {desc or 'Sin detalle'}", size=12),
                ft.Divider(),
                ft.Text("Firma: Entregado / Recibido Conforme", size=11, italic=True, color="grey")
            ]),
            actions=[ft.Button("Cerrar", bgcolor="#5d4037", color="white", on_click=cerrar)]
        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    def ver_reporte(e):
        sede, enc, ced = gcfg()
        conn = sqlite3.connect(DB_NAME)
        filas = conn.cursor().execute("SELECT fecha, tipo, categoria, monto FROM movimientos WHERE usuario_id = ? ORDER BY id DESC", (uid,)).fetchall()
        conn.close()
        ing = sum(float(m) for _, t, _, m in filas if t == "Ingreso")
        egr = sum(float(m) for _, t, _, m in filas if t == "Egreso")
        saldo = ing - egr
        items = [ft.Text(sede.upper(), size=11, weight=ft.FontWeight.BOLD, color="#5d4037"), ft.Text(f"Emitido: {datetime.now().strftime('%d/%m/%Y %H:%M')}", size=10, color="grey"), ft.Divider()]
        for fec, tip, cat, mon in filas:
            es_i = tip == "Ingreso"
            items.append(ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text(f"{cat} ({fec[:5]})", size=11, expand=True, overflow=ft.TextOverflow.ELLIPSIS), ft.Text(f"{'+' if es_i else '-'}Bs. {formatear_moneda(mon)}", size=11, weight=ft.FontWeight.BOLD, color="#2e7d32" if es_i else "#c62828")]))
        items.extend([ft.Divider(), ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("SALDO EN CAJA:", weight=ft.FontWeight.BOLD, size=12), ft.Text(f"Bs. {formatear_moneda(saldo)}", weight=ft.FontWeight.BOLD, size=13, color="#2e7d32" if saldo >= 0 else "#c62828")]), ft.Divider(), ft.Text(f"Firma: {enc}", size=11, weight=ft.FontWeight.BOLD, color="#5d4037"), ft.Text(f"Responsable Control Diario - C.I.: {ced}", size=10, color="grey")])
        def cerrar(ev):
            dlg.open = False
            page.update()
        dlg = ft.AlertDialog(title=ft.Text("REPORTE CONTABLE OFICIAL", size=14, weight=ft.FontWeight.BOLD), content=ft.Column(scroll=ft.ScrollMode.AUTO, tight=True, spacing=6, controls=items), actions=[ft.Button("Cerrar", bgcolor="#5d4037", color="white", on_click=cerrar)])
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    def cargar():
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        todas = c.execute("SELECT tipo, monto FROM movimientos WHERE usuario_id = ?", (uid,)).fetchall()
        ing = sum(float(m) for t, m in todas if t == "Ingreso")
        egr = sum(float(m) for t, m in todas if t == "Egreso")
        q = "SELECT id, fecha, tipo, categoria, descripcion, monto FROM movimientos WHERE usuario_id = ?"
        p = [uid]
        if txt_fec.value.strip():
            q += " AND fecha LIKE ?"
            p.append(f"%{txt_fec.value.strip()}%")
        if dd_fcat.value != "Todas":
            q += " AND categoria = ?"
            p.append(dd_fcat.value)
        filas = c.execute(q + " ORDER BY id DESC", tuple(p)).fetchall()
        conn.close()
        lbl_saldo.value = f"Bs. {formatear_moneda(ing - egr)}"
        lista.controls.clear()
        for mov_id, fec, tip, cat, desc, mon in filas:
            es_i = tip == "Ingreso"
            col = "#2e7d32" if es_i else "#c62828"
            lista.controls.append(ft.Card(content=ft.Container(padding=10, content=ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Row(expand=True, spacing=8, controls=[ft.Icon(ft.Icons.ARROW_CIRCLE_UP if es_i else ft.Icons.ARROW_CIRCLE_DOWN, color=col, size=24), ft.Column(expand=True, spacing=1, controls=[ft.Text(cat, weight=ft.FontWeight.BOLD, size=13, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS), ft.Text(desc or "Sin detalle", size=11, color="grey", max_lines=1, overflow=ft.TextOverflow.ELLIPSIS), ft.Text(fec[:10], size=10, color="grey")])]), ft.Row(spacing=0, controls=[ft.Text(f"{'+' if es_i else '-'}Bs. {formatear_moneda(mon)}", weight=ft.FontWeight.BOLD, color=col, size=12), ft.IconButton(icon=ft.Icons.DELETE_OUTLINE, icon_color="red", icon_size=18, on_click=lambda e, m=mov_id: borrar(m))])]))))
        page.update()

    def guardar(e):
        try:
            m = float(txt_monto.value.replace(",", "."))
            if m <= 0:
                raise ValueError
        except Exception:
            msg("Monto inválido", "red")
            return
        sede, _, _ = gcfg()
        ah = datetime.now()
        fec = ah.strftime("%d/%m/%Y") + " " + MESES.get(ah.strftime("%m"), "") + " " + ah.strftime("%H:%M")
        conn = sqlite3.connect(DB_NAME)
        conn.cursor().execute("INSERT INTO movimientos (usuario_id, fecha, tipo, categoria, descripcion, monto) VALUES (?, ?, ?, ?, ?, ?)", (uid, fec, dd_tipo.value, dd_cat.value, txt_desc.value.strip(), m))
        conn.commit()
        conn.close()
        egr_data = (sede, fec, dd_cat.value, txt_desc.value.strip(), m)
        is_egr = dd_tipo.value == "Egreso"
        txt_monto.value = ""
        txt_desc.value = ""
        nav.selected_index = 0
        cont.content = v0
        cargar()
        if is_egr:
            def cerrar_dlg(ev):
                dlg.open = False
                page.update()
            def abrir_rec(ev):
                dlg.open = False
                page.update()
                ver_recibo(*egr_data)
            dlg = ft.AlertDialog(title=ft.Text("Recibo de Pago", weight=ft.FontWeight.BOLD), content=ft.Text("¿Deseas ver el comprobante oficial de este egreso?"), actions=[ft.TextButton("No", on_click=cerrar_dlg), ft.Button("Sí", bgcolor="#5d4037", color="white", on_click=abrir_rec)])
            page.overlay.append(dlg)
            dlg.open = True
            page.update()
        else:
            msg("Ingreso guardado correctamente")

    hdr = ft.Container(padding=ft.Padding.symmetric(horizontal=14, vertical=10), bgcolor="#5d4037", border_radius=ft.BorderRadius.only(bottom_left=16, bottom_right=16), content=ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[ft.Column(expand=True, spacing=2, controls=[lbl_sede, ft.Text("Saldo Actual en Caja", color="white", size=12)]), lbl_saldo]))
    v0 = ft.Column(expand=True, controls=[hdr, ft.Container(padding=ft.Padding.symmetric(horizontal=10, vertical=5), content=ft.Row(controls=[txt_fec, dd_fcat])), lista])
    b_g = ft.Button("Guardar Movimiento", icon=ft.Icons.SAVE, bgcolor="#6d4c41", color="white", height=48, on_click=guardar)
    v1 = ft.Container(padding=20, expand=True, content=ft.Column(scroll=ft.ScrollMode.AUTO, spacing=14, controls=[ft.Text("Nuevo Registro Contable", size=19, weight=ft.FontWeight.BOLD), dd_tipo, dd_cat, txt_monto, txt_desc, b_g]))
    b_r = ft.Button("Ver Reporte Contable Oficial", icon=ft.Icons.PICTURE_AS_PDF, bgcolor="#8d6e63", color="white", height=48, on_click=ver_reporte)
    b_cfg = ft.Button("Guardar Configuración", icon=ft.Icons.SAVE, bgcolor="#5d4037", color="white", on_click=scfg)
    v2 = ft.Container(padding=20, expand=True, content=ft.Column(scroll=ft.ScrollMode.AUTO, spacing=12, controls=[ft.Text("Reportes y Configuración", size=19, weight=ft.FontWeight.BOLD), b_r, ft.Divider(), dd_tema, ft.Divider(), ft.Text("Configurar Sede y Responsable", weight=ft.FontWeight.BOLD), t_s, t_e, t_c, b_cfg]))
    cont = ft.Container(content=v0, expand=True)

    def tab(e):
        cont.content = [v0, v1, v2][nav.selected_index]
        if nav.selected_index == 0:
            cargar()
        else:
            page.update()

    def tema(n):
        t = TEMAS.get(n, TEMAS["Carmelita Clásico"])
        page.theme_mode = ft.ThemeMode.DARK if t["dark"] else ft.ThemeMode.LIGHT
        page.bgcolor = t["bg"]
        hdr.bgcolor = t["header"]
        b_g.bgcolor = t["btn"]
        b_r.bgcolor = t["btn"]
        b_cfg.bgcolor = t["header"]
        page.update()

    nav = ft.NavigationBar(selected_index=0, on_change=tab, destinations=[ft.NavigationBarDestination(icon=ft.Icons.LIST_ALT, label="Movimientos"), ft.NavigationBarDestination(icon=ft.Icons.ADD_CIRCLE, label="Registrar"), ft.NavigationBarDestination(icon=ft.Icons.SETTINGS, label="Reportes")])
    page.add(ft.SafeArea(content=cont, expand=True), nav)
    tema("Carmelita Clásico")
    cargar()

if __name__ == "__main__":
    ft.run(main)
