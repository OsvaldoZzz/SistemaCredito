from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import os

def generar_estado_cartera(clientes, prestamos_por_cliente, filename="estado_cartera.pdf"):
    doc = SimpleDocTemplate(filename, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()

    # Título
    elements.append(Paragraph("ESTADO DE CARTERA", styles['Title']))
    elements.append(Spacer(1, 12))

    # Datos de la tabla
    data = [["Cliente", "Cédula", "Monto Total Préstamos", "Estado"]]

    for cliente in clientes:
        cedula = cliente["cedula"]
        prestamos = prestamos_por_cliente.get(cedula, [])
        total = sum([float(p["monto"].replace("C$", "").replace(",", "").strip()) for p in prestamos if "monto" in p])

        # Simplificación del estado: si hay préstamos, está "Activo"
        estado = "Activo" if prestamos else "Sin Préstamos"

        data.append([
            cliente["nombre"],
            cedula,
            f"C$ {total:,.2f}",
            estado
        ])

    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))

    elements.append(table)
    doc.build(elements)

    # Abrir el archivo automáticamente en Windows
    os.startfile(filename)

def generar_reporte_cobranza(clientes, prestamos_por_cliente, filename="reporte_cobranza.pdf"):
    doc = SimpleDocTemplate(filename, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph("REPORTE FINANCIERO DE COBRANZA", styles['Title']))
    elements.append(Spacer(1, 12))

    data = [["ID Préstamo", "Cliente", "Monto", "Plazo", "Estado"]]

    for cliente in clientes:
        cedula = cliente["cedula"]
        prestamos = prestamos_por_cliente.get(cedula, [])
        for p in prestamos:
            data.append([
                p["id"],
                cliente["nombre"],
                p["monto"],
                p["plazo"],
                p["estado"]
            ])

    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.blue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))

    elements.append(table)
    doc.build(elements)
    os.startfile(filename)

def generar_recibo_pago(cliente, prestamo_id, monto_abono, filename="recibo_pago.pdf"):
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter

    # Diseño del recibo
    c.setStrokeColor(colors.black)
    c.rect(50, height - 300, 500, 250) # Borde del recibo

    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2, height - 80, "RECIBO DE PAGO")

    c.setFont("Helvetica", 12)
    c.drawString(70, height - 120, f"Fecha: {os.popen('date /t').read().strip()}")
    c.drawString(70, height - 140, f"Cliente: {cliente['nombre']}")
    c.drawString(70, height - 160, f"Cédula: {cliente['cedula']}")
    c.drawString(70, height - 180, f"ID Préstamo: {prestamo_id}")

    c.setFont("Helvetica-Bold", 14)
    c.drawString(70, height - 220, f"MONTO ABONADO: C$ {monto_abono}")

    c.setFont("Helvetica-Oblique", 10)
    c.drawString(70, height - 260, "Gracias por su pago.")

    c.showPage()
    c.save()

    os.startfile(filename)