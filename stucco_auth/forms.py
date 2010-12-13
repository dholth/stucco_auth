"""
Experimental views for the deform forms library.
"""

import colander
import deform

from pkg_resources import resource_filename
deform_template_dir = resource_filename('stucco_auth', 'templates/deform/')
deform.Form.set_zpt_renderer(
        [deform_template_dir]
        )

class Schema(colander.Schema):
    text = colander.SchemaNode(
            colander.String,
            description='Enter some text')

    text2 = colander.SchemaNode(
            colander.String,
            description='Enter some more text')

schema = Schema()

def view_form(request):
    """Test deform."""
    form = deform.Form(schema, buttons=('submit',))
    return dict(form=form.render({}))