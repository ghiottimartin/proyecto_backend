import cgi
import io
from xhtml2pdf import pisa
from django.template.loader import get_template
from django.http import HttpResponse


def render_to_pdf(template_src, context_dict):
    template = get_template(template_src)
    html = template.render(context_dict)
    result = io.BytesIO()

    pdf = pisa.pisaDocument(io.BytesIO(html.encode("ISO-8859-1")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return HttpResponse('Hubo un error al general el pdf <pre>%s</pre>' % cgi.escape(html))
