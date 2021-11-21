import cgi
import io
from xhtml2pdf import pisa
from django.template.loader import get_template
from django.http import HttpResponse
from django.http import FileResponse
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch


def render_to_pdf(template_src, context_dict):
    template = get_template(template_src)
    html = template.render(context_dict)
    result = io.BytesIO()

    pdf = pisa.pisaDocument(io.BytesIO(html.encode("ISO-8859-1")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return HttpResponse('Hubo un error al general el pdf <pre>%s</pre>' % cgi.escape(html))


def pdf_venta(venta):
    # Creo un buffer de salida
    buffer = io.BytesIO()

    # Creo pdf
    pdf = canvas.Canvas(buffer)

    # Defino título de pdf
    nombre = venta["nombre"]
    pdf.setTitle(nombre)

    # Defino tamaño de pdf
    # TODO calcular la altura
    width = 200
    height = 300
    pdf.setPageSize((width, height))

    # Agrego línea id de venta
    id_venta = str(venta["id_texto_limpio"])
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(70, 275, id_venta)

    # Agrego la fecha.
    pdf.setFont("Helvetica-Bold", 10)
    fecha_texto = "Fecha: " + venta['fecha_texto']
    pdf.drawString(80, 250, fecha_texto)

    # Agrego texto cantidad / precio unitario
    pdf.drawString(5, 210, "CANT ./ PRECIO UNIT.")
    pdf.drawString(5, 195, "DESCRIPCION")
    pdf.drawString(150, 195, "IMPORTE")

    altura = 180
    lineas = venta["lineas"]
    pdf.setFont("Helvetica", 10)
    for linea in lineas:
        cantidad = linea['cantidad']
        subtotal = linea['precio_texto']
        cantidad_precio = str(cantidad) + " x " + str(subtotal)
        pdf.drawString(5, altura, cantidad_precio)

        altura -= 15
        producto = linea['producto']
        id_producto = producto['id']
        nombre = producto['nombre']
        id_nombre = "(" + str(id_producto) + ")  " + nombre
        pdf.drawString(5, altura, id_nombre)

        total = str(linea['total_texto'])
        pdf.drawString(150, altura, total)

        altura -= 15

    total_texto = venta['total_texto']
    altura_calculada = 180 - len(lineas) * 30 - 10
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(105, altura_calculada, "TOTAL: " + total_texto)

    # Cierro y guardo el pdf
    pdf.showPage()
    pdf.save()

    # FileResponse sets the Content-Disposition header so that browsers
    # present the option to save the file.
    buffer.seek(0)

    # Defino nombre de archivo.
    file_name = nombre + ".pdf"
    return FileResponse(buffer, as_attachment=True, filename=file_name)
