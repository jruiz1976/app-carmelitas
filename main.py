import sqlite3, os, webbrowser
from datetime import datetime
import flet as ft

BASE_DIR = os.getenv("FLET_APP_STORAGE_DATA", os.getcwd())
DB_NAME = os.path.join(BASE_DIR, 'sistema_carmelitas.db')
P = chr(37)
MESES = {'01':'Enero','02':'Febrero','03':'Marzo','04':'Abril','05':'Mayo','06':'Junio','07':'Julio','08':'Agosto','09':'Septiembre','10':'Octubre','11':'Noviembre','12':'Diciembre'}
TEMAS = {'Carmelita Clásico':{'bg':'#f5efe6','header':'#5d4037','btn':'#6d4c41','dark':False},'Azul Institucional':{'bg':'#f0f4f8','header':'#1976d2','btn':'#2196f3','dark':False},'Verde Esperanza':{'bg':'#e8f5e9','header':'#2e7d32','btn':'#388e3c','dark':False},'Vino Formal':{'bg':'#fce4ec','header':'#880e4f','btn':'#ad1457','dark':False},'Modo Oscuro':{'bg':'#121212','header':'#1f1f1f','btn':'#00897b','dark':True}}

def inicializar_base_datos():
    conn = sqlite3.connect(DB_NAME)
    conn.cursor().execute('CREATE TABLE IF NOT EXISTS movimientos (id INTEGER PRIMARY KEY AUTOINCREMENT, usuario_id TEXT, fecha TEXT, tipo TEXT, categoria TEXT, descripcion TEXT, monto REAL)')
    conn.cursor().execute('CREATE TABLE IF NOT EXISTS cfg(id INT PRIMARY KEY, sede TEXT, enc TEXT, ced TEXT)'); conn.cursor().execute('INSERT OR IGNORE INTO cfg VALUES(1, "Comunidad Carmelitas Centro", "Hns. Yerica Blanco", "V-12.345.678")'); conn.commit(); conn.close()

def formatear_moneda(v):
    return f'{v:,.2f}'.replace(',','X').replace('.',',').replace('X','.')
def generar_recibo_html(comunidad, fecha, categoria, descripcion, monto):
    n_recibo = os.path.join(BASE_DIR, f'recibo_{datetime.now().strftime(P+"Y"+P+"m"+P+"d_"+P+"H"+P+"M"+P+"S")}.html')
    mf = formatear_moneda(monto)
    desc_val = descripcion if descripcion else 'Sin detalles adicionales.'
    logo = '<img src="file:///' + os.path.join(BASE_DIR, 'escudo.png').replace(chr(92), '/') + '" style="width:70px;height:auto;margin-bottom:8px"><br>' if os.path.exists(os.path.join(BASE_DIR, 'scudo.png')) else ''
    html = '<html><body style="font-family:Arial;color:#333;padding:20px"><div style="border:2px solid #5d4037;padding:20px;border-radius:8px;max-width:600px;margin:auto"><div style="text-align:center;border-bottom:2px solid #5d4037;padding-bottom:12px;margin-bottom:15px">' + logo + '<h2 style="color:#5d4037;margin:0">COMPROBANTE DE PAGO</h2><p style="color:#666;font-size:12px;margin:4px 0">CONGREGACIÓN HERMANAS CARMELITAS - ' + comunidad.upper() + '</p><div style="background:#f5efe6;border:2px dashed #5d4037;padding:8px 18px;font-size:18px;font-weight:bold;color:#c62828;display:inline-block;margin-top:8px">Bs. ' + mf + '</div></div><p><b>Fecha y Hora:</b> ' + fecha + '</p><p><b>Concepto / Categoría:</b> ' + categoria + '</p><p><b>Descripción:</b> ' + desc_val + '</p><div style="margin-top:60px;display:flex;justify-content:space-around"><div style="text-align:center;width:40%;border-top:1px solid #333;padding-top:6px;font-size:12px;font-weight:bold">Entregado Por</div><div style="text-align:center;width:40%;border-top:1px solid #333;padding-top:6px;font-size:12px;font-weight:bold">Recibido Conforme</div></div></div></body></html>'
    open(n_recibo,'w',encoding='utf-8').write(html)
    return n_recibo

def exportar_reporte_html(comunidad, uid, encargada='Hna. Yerica Blanco', cedula='V-12.345.678'):
    n_arch = os.path.join(BASE_DIR, f'reporte_{comunidad.replace(" ","_").lower()}.html')
    conn = sqlite3.connect(DB_NAME); c = conn.cursor()
    c.execute('SELECT fecha, tipo, categoria, descripcion, monto FROM movimientos WHERE usuario_id = ? ORDER BY id DESC', (uid,))
    filas = c.fetchall()
    c.execute('SELECT SUM(monto) FROM movimientos WHERE usuario_id = ? AND tipo = "Ingreso"', (uid,)); ing = (c.fetchone()[0] or 0.0)
    c.execute('SELECT SUM(monto) FROM movimientos WHERE usuario_id = ? AND tipo = "Egreso"', (uid,)); egr = (c.fetchone()[0] or 0.0)
    conn.close(); saldo = ing - egr
    logo = f'<img src="file:///{os.path.join(BASE_DIR,"escudo.png").replace(chr(92),"/")}" style="width:65px;height:auto;margin-right:18px">' if os.path.exists(os.path.join(BASE_DIR,'escudo.png')) else ''
    filas_html = ''.join(f'<tr><td style="padding:9px 12px;border-bottom:1px solid #eee">{fec}</td><td style="padding:9px 12px;border-bottom:1px solid #eee">{tip}</td><td style="padding:9px 12px;border-bottom:1px solid #eee">{cat}</td><td style="padding:9px 12px;border-bottom:1px solid #eee">{det or "-"}</td><td style="padding:9px 12px;border-bottom:1px solid #eee;text-align:right;font-weight:bold;color:{"#2e7d32" if tip=="Ingreso" else "#c62828"}">{"+" if tip=="Ingreso" else "-"}Bs. {formatear_moneda(mon)}</td></tr>' for fec, tip, cat, det, mon in filas)
    fec_rep = datetime.now().strftime(P+'d/'+P+'m/'+P+'Y '+P+'H:'+P+'M')
    col_s = '#c62828' if saldo < 0 else '#2e7d32'
    mon_s = formatear_moneda(saldo)
    html = f'<html><body style=font-family:Arial,sans-serif;color:#333;padding:30px><div style="display:flex;align-items:center;border-bottom:2px solid #5d4037;padding-bottom:15px;margin-bottom:18px">{logo}<div><h1 style="color:#5d4037;font-size:20px;margin:0">REPORTE CONTABLE OFICIAL</h1><h2 style="color:#666;font-size:12px;margin:4px 0 0 0">CONGREGACIÓN HERMANAS CARMELITAS - {comunidad.upper()}</h2></div></div><div style="background:#f5efe6;padding:10px 15px;display:flex;justify-content:space-between;font-size:12px;margin-bottom:20px"><span><b>Fecha:</b> {fec_rep}</span><span>Generado por: <b>Control Interno</b></span></div><table style="width:100{P};border-collapse:collapse;margin-bottom:30px"><thead><tr style="background:#5d4037;color:#fff;font-size:12px"><th style="padding:10px 12px;text-align:left">FECHA</th><th style="padding:10px 12px;text-align:left">TIPO</th><th style="padding:10px 12px;text-align:left">CATEGORÍA</th><th style="padding:10px 12px;text-align:left">DESCRIPCIÓN</th><th style="padding:10px 12px;text-align:right">MONTO</th></tr></thead><tbody>{filas_html}<tr style="font-weight:bold;border-top:2px solid #5d4037;background:#f5efe6;font-size:13px"><td colspan=4 style="padding:12px;text-align:right">SALDO TOTAL EN CAJA:</td><td style="padding:12px;text-align:right;color:{col_s}">Bs. {mon_s}</td></tr></tbody></table><div style="margin-top:70px;text-align:center"><div style="display:inline-block;width:280px;border-top:1px solid #333;padding-top:8px"><div style="font-size:13px;font-weight:bold">{encargada}</div><div style="font-size:11px;color:#555">Responsable del Control Diario - C.I.: {cedula}</div></div></div><script>window.onload=function(){{window.print();}}</script></body></html>'
    open(n_arch,'w',encoding='utf-8').write(html)
    return n_arch

def main(page: ft.Page):
    inicializar_base_datos()
    uid, com = 'carmelitas1', 'Comunidad Carmelitas Centro'
    cats = ['Diezmo','Ofrenda','Servicios Públicos','Ayuda Social','Mantenimiento','Otros']
    page.title = 'Contabilidad Carmelitas'; page.padding = 0
    def msg(t, col='green'):
        sb = ft.SnackBar(ft.Text(t, color='white'), bgcolor=col); page.overlay.append(sb); sb.open = True; page.update()
    lbl_saldo = ft.Text('Bs. 0,00', size=22, weight=ft.FontWeight.BOLD, color='white')
    lista = ft.ListView(expand=True, spacing=8, padding=10)
    txt_fec = ft.TextField(label='Filtrar fecha', dense=True, expand=True, on_change=lambda e: cargar())
    dd_fcat = ft.Dropdown(label='Categoría', dense=True, width=150, value='Todas', options=[ft.dropdown.Option('Todas')]+[ft.dropdown.Option(c) for c in cats], on_select=lambda e: cargar())
    dd_tipo = ft.Dropdown(label='Tipo', value='Ingreso', options=[ft.dropdown.Option('Ingreso'),ft.dropdown.Option('Egreso')])
    dd_cat = ft.Dropdown(label='Categoría', value='Ofrenda', options=[ft.dropdown.Option(c) for c in cats])
    txt_monto = ft.TextField(label='Monto (Bs.)', keyboard_type=ft.KeyboardType.NUMBER)
    txt_desc = ft.TextField(label='Descripción (Opcional)', multiline=True, min_lines=2, max_lines=3)
    dd_tema = ft.Dropdown(label='Tema Visual', value='Carmelita Clásico', options=[ft.dropdown.Option(t) for t in TEMAS], on_select=lambda e: tema(e.control.value))
    def borrar(mid):
        conn = sqlite3.connect(DB_NAME); conn.cursor().execute('DELETE FROM movimientos WHERE id = ?', (mid,)); conn.commit(); conn.close(); cargar(); msg('Eliminado','red')
    def cargar():
        lista.controls.clear(); conn = sqlite3.connect(DB_NAME); c = conn.cursor()
        q, p = 'SELECT id, fecha, tipo, categoria, descripcion, monto FROM movimientos WHERE usuario_id = ?', [uid]
        if txt_fec.value.strip(): q += ' AND fecha LIKE ?'; p.append(P+txt_fec.value.strip()+P)
        if dd_fcat.value != 'Todas': q += ' AND categoria = ?'; p.append(dd_fcat.value)
        c.execute(q+' ORDER BY id DESC', tuple(p)); filas = c.fetchall()
        c.execute('SELECT SUM(monto) FROM movimientos WHERE usuario_id = ? AND tipo = "Ingreso"', (uid,)); ing = c.fetchone()[0] or 0.0
        c.execute('SELECT SUM(monto) FROM movimientos WHERE usuario_id = ? AND tipo = "Egreso"', (uid,)); egr = c.fetchone()[0] or 0.0
        conn.close(); lbl_saldo.value = f'Bs. {formatear_moneda(ing-egr)}'
        for r in filas:
            es_i = r[2] == 'Ingreso'; col = '#2e7d32' if es_i else '#c62828'
            lista.controls.append(ft.Card(content=ft.Container(padding=12, content=ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Row(controls=[ft.Icon(ft.Icons.ARROW_CIRCLE_UP if es_i else ft.Icons.ARROW_CIRCLE_DOWN, color=col, size=30), ft.Column(spacing=2, controls=[ft.Text(r[3], weight=ft.FontWeight.BOLD), ft.Text(r[4] or 'Sin detalle', size=12, color='grey'), ft.Text(r[1], size=10, color='grey')])]), ft.Row(controls=[ft.Text(f'{"+" if es_i else "-"}Bs. {formatear_moneda(r[5])}', weight=ft.FontWeight.BOLD, color=col), ft.IconButton(icon=ft.Icons.DELETE_OUTLINE, icon_color='red', on_click=lambda e, m=r[0]: borrar(m))])]))))
        page.update()
    def guardar(e):
        try:
            m = float(txt_monto.value.replace(',','.'))
            if m <= 0: raise ValueError
        except: msg('Monto inválido','red'); return
        ah = datetime.now(); fec = ah.strftime(P+'d/'+P+'m/'+P+'Y')+' '+MESES.get(ah.strftime(P+'m'),'')+' '+ah.strftime(P+'H:'+P+'M')
        conn = sqlite3.connect(DB_NAME); conn.cursor().execute('INSERT INTO movimientos (usuario_id, fecha, tipo, categoria, descripcion, monto) VALUES (?,?,?,?,?,?)', (uid, fec, dd_tipo.value, dd_cat.value, txt_desc.value.strip(), m)); conn.commit(); conn.close()
        egr_data = (com, fec, dd_cat.value, txt_desc.value.strip(), m)
        is_egr = (dd_tipo.value == 'Egreso')
        txt_monto.value = ''; txt_desc.value = ''; cargar(); nav.selected_index = 0; tab(None)
        if is_egr:
            def cerrar_dlg(e):
                dlg.open = False; page.update()
            def abrir_rec(e):
                dlg.open = False; page.update()
                ruta = generar_recibo_html(*egr_data)
                webbrowser.open('file://' + os.path.abspath(ruta))
            dlg = ft.AlertDialog(
                title=ft.Text('Recibo de Pago', weight=ft.FontWeight.BOLD),
                content=ft.Text('¿Deseas generar el recibo de pago oficial para este egreso?'),
                actions=[
                    ft.TextButton('No', on_click=cerrar_dlg),
                    ft.Button('Sí', bgcolor='#5d4037', color='white', on_click=abrir_rec)
                ]
            )
            page.overlay.append(dlg); dlg.open = True; page.update()
        else:
            msg('Ingreso guardado correctamente')
    hdr = ft.Container(padding=ft.Padding.symmetric(horizontal=20, vertical=10), bgcolor="#5d4037", border_radius=ft.BorderRadius.only(bottom_left=16, bottom_right=16), content=ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[ft.Column(spacing=2, controls=[ft.Text(com.upper(), color="white70", size=10, weight=ft.FontWeight.BOLD), ft.Text("Saldo Actual en Caja", color="white", size=13)]), lbl_saldo]))
    v0 = ft.Column(expand=True, controls=[hdr, ft.Container(padding=ft.Padding.symmetric(horizontal=10, vertical=5), content=ft.Row(controls=[txt_fec, dd_fcat])), lista])
    b_g = ft.Button('Guardar Movimiento', icon=ft.Icons.SAVE, bgcolor='#6d4c41', color='white', height=48, on_click=guardar)
    v1 = ft.Container(padding=20, expand=True, content=ft.Column(spacing=15, controls=[ft.Text('Nuevo Registro Contable', size=20, weight=ft.FontWeight.BOLD), dd_tipo, dd_cat, txt_monto, txt_desc, b_g]))
    b_r = ft.Button('Generar Reporte Contable (HTML)', icon=ft.Icons.PICTURE_AS_PDF, bgcolor='#8d6e63', color='white', height=48, on_click=lambda e: webbrowser.open('file://' + os.path.abspath(exportar_reporte_html(t_s.value, uid, t_e.value, t_c.value))))
    v2 = ft.Container(padding=20, expand=True, content=ft.Column(scroll=ft.ScrollMode.AUTO, spacing=12, controls=[ft.Text('Reportes y Configuración', size=20, weight=ft.FontWeight.BOLD), b_r, ft.Divider(), ft.Text('Apariencia', size=16, weight=ft.FontWeight.BOLD), dd_tema]))
    def gcfg():
        cn=sqlite3.connect(DB_NAME); r=cn.cursor().execute('SELECT sede,enc,ced FROM cfg WHERE id=1').fetchone(); cn.close(); return r or ('Comunidad Carmelitas Centro','Hna. Yerica Blanco','V-12.345.678')
    s0,e0,c0=gcfg(); t_s=ft.TextField(label='Comunidad / Sede',value=s0,dense=True); t_e=ft.TextField(label='Hermana Responsable',value=e0,dense=True); t_c=ft.TextField(label='Cedula',value=c0,dense=True)
    def scfg(e):
        cn=sqlite3.connect(DB_NAME); cn.cursor().execute('UPDATE cfg SET sede=?,enc=?,ced=? WHERE id=1',(t_s.value,t_e.value,t_c.value)); cn.commit(); cn.close(); msg('Configuracion guardada')
    v2.content.controls.extend([ft.Divider(),ft.Text('Configurar Sede y Responsable',weight=ft.FontWeight.BOLD),t_s,t_e,t_c,ft.Button('Guardar Configuracion',bgcolor='#5d4037',color='white',on_click=scfg)])
    cont = ft.Container(content=v0, expand=True)
    def tab(e): cont.content = [v0, v1, v2][nav.selected_index]; page.update()
    def tema(n):
        t = TEMAS.get(n, TEMAS['Carmelita Clásico']); page.theme_mode = ft.ThemeMode.DARK if t['dark'] else ft.ThemeMode.LIGHT
        page.bgcolor = t['bg']; hdr.bgcolor = t['header']; b_g.bgcolor = t['btn']; b_r.bgcolor = t['btn']; page.update()
    nav = ft.NavigationBar(selected_index=0, on_change=tab, destinations=[ft.NavigationBarDestination(icon=ft.Icons.LIST_ALT, label='Movimientos'), ft.NavigationBarDestination(icon=ft.Icons.ADD_CIRCLE, label='Registrar'), ft.NavigationBarDestination(icon=ft.Icons.SETTINGS, label='Reportes')])
    page.add(cont, nav); tema('Carmelita Clásico'); cargar()

if __name__ == '__main__':
    ft.run(main, view=ft.AppView.WEB_BROWSER, port=8550, assets_dir=BASE_DIR)
