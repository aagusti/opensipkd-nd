from datetime import datetime
from pyramid.view import view_config
from pyramid.httpexceptions import (
    HTTPFound,
    HTTPForbidden,
    )
from pyramid.security import (
    remember,
    forget,
    authenticated_userid,
    )
import transaction
import colander
from deform import (
    Form,
    ValidationFailure,
    widget,
    )
from ...tools import create_now
from ...models import (
    DBSession,
    )


##################
# Home Nota Dinas#
##################
@view_config(route_name='notadinas', renderer='templates/home.pt', permission='home')
def view_home(request):
    return dict(project='notadinas')



