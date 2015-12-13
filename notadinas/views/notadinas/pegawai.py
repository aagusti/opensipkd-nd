from email.utils import parseaddr
from sqlalchemy import not_, or_
from pyramid.view import (
    view_config,
    )
from pyramid.httpexceptions import (
    HTTPFound,
    )
import colander
from deform import (
    Form,
    widget,
    ValidationFailure,
    )
from ...models import(
    DBSession, User
    )
from ...models.pemda import (
    Unit, Urusan
    )
from ...models.notadinas import (
    Jabatan, Pegawai, Job
    )
from datatables import ColumnDT, DataTables
from datetime import datetime
from ...tools import create_now

SESS_ADD_FAILED = 'pegawai add failed'
SESS_EDIT_FAILED = 'pegawai edit failed'    
	
########                    
# List #
########    
@view_config(route_name='notadinas-pegawai', renderer='templates/pegawai/list.pt',
             permission='notadinas-pegawai')
def view_list(request):
    #rows = DBSession.query(User).filter(User.id > 0).order_by('email')
    return dict(project='Notadinas')
    
##########                    
# Action #
##########    
@view_config(route_name='notadinas-pegawai-act', renderer='json',
             permission='notadinas-pegawai-act')
def pegawai_act(request):
    ses = request.session
    req = request
    params = req.params
    url_dict = req.matchdict
    
    if url_dict['act']=='grid':
        columns = []
        columns.append(ColumnDT('id'))
        columns.append(ColumnDT('kode'))
        columns.append(ColumnDT('nama'))
        columns.append(ColumnDT('jabatans.nama'))
        columns.append(ColumnDT('units.nama'))
        
        query = DBSession.query(Pegawai)
        rowTable = DataTables(req, Pegawai, query, columns)
        return rowTable.output_result()

    elif url_dict['act']=='grid1':
        cari = 'cari' in params and params['cari'] or ''
        columns = []
        columns.append(ColumnDT('id'))
        columns.append(ColumnDT('kode'))
        columns.append(ColumnDT('nama'))
        columns.append(ColumnDT('jabatans.nama'))
        columns.append(ColumnDT('units.nama'))
        
        query = DBSession.query(Pegawai
                        ).filter(Pegawai.unit_id==Unit.id,
                                 Pegawai.jabatan_id==Jabatan.id,
                                 or_(Pegawai.kode.ilike('%%%s%%' % cari),
                                     Pegawai.nama.ilike('%%%s%%' % cari),
                                     Unit.nama.ilike('%%%s%%' % cari),
                                     Jabatan.nama.ilike('%%%s%%' % cari),)
                        )
        rowTable = DataTables(req, Pegawai, query, columns)
        return rowTable.output_result()
        
    elif url_dict['act']=='hon':
        term = 'term' in params and params['term'] or '' 
        rows = DBSession.query(Pegawai.id, Pegawai.kode, Pegawai.nama
                       ).filter(Pegawai.nama.ilike('%%%s%%' % term) 
                       ).all()
        r = []
        for k in rows:
            d={}
            d['id']      = k[0]
            d['value']   = k[2]
            d['kode']    = k[1]
            r.append(d)
        return r  
		
    elif url_dict['act']=='hon_pegawai_penerima':
        term = 'term' in params and params['term'] or '' 
        rows = DBSession.query(Pegawai.id, Pegawai.kode, Pegawai.nama, Pegawai.user_id
                       ).filter(Pegawai.user_id!=None,
                                Pegawai.nama.ilike('%%%s%%' % term) 
                       ).all()
        r = []
        for k in rows:
            d={}
            d['id']      = k[0]
            d['value']   = k[2]
            d['kode']    = k[1]
            d['user']    = k[3]
            r.append(d)
        return r  
		
    elif url_dict['act']=='hok':
        term = 'term' in params and params['term'] or '' 
        rows = DBSession.query(Pegawai.id, Pegawai.kode
                       ).filter(Pegawai.kode.ilike('%%%s%%' % term) 
                       ).all()
        r = []
        for k in rows:
            d={}
            d['id']          = k[0]
            d['value']       = k[1]
            r.append(d)
        return r      
    
#######    
# Add #
#######
def form_validator(form, value):
    def err_kode():
        raise colander.Invalid(form,
            'Kode %s sudah digunakan oleh ID %d' % (
                value['kode'], found.id))
    def err_nama():
        raise colander.Invalid(form,
            'Nama %s sudah digunakan oleh ID %d' % (
                value['nama'], found.id))
                
    if 'id' in form.request.matchdict:
        uid = form.request.matchdict['id']
        q = DBSession.query(Pegawai).filter_by(id=uid)
        pegawai = q.first()
    else:
        pegawai = None
        
    q = DBSession.query(Pegawai).filter_by(kode=value['kode'])
    found = q.first()
    if pegawai:
        if found and found.id != pegawai.id:
            err_kode()
    elif found:
        err_kode()
        
    if 'nama' in value: # optional
        found = Pegawai.get_by_nama(value['nama'])
        if pegawai:
            if found and found.id != pegawai.id:
                err_nama()
        elif found:
            err_nama()
   

class AddSchema(colander.Schema):  
    unit_id    = colander.SchemaNode(
                    colander.Integer(),
                    oid = "unit_id")
    unit_nm    = colander.SchemaNode(
                    colander.String(),
                    oid = "unit_nm",
                    title = "Unit")
    kode       = colander.SchemaNode(
                    colander.String(),
                    oid = "kode",
                    title = "NIP",)
    nama       = colander.SchemaNode(
                    colander.String(),
                    oid = "nama",
                    title = "Nama",)
    jabatan_id = colander.SchemaNode(
                    colander.Integer(),
                    oid="jabatan_id",
                    missing=colander.drop)
    jabatan_nm = colander.SchemaNode(
                    colander.String(),
                    #missing=colander.drop,
                    oid="jabatan_nm",
                    title="Jabatan")
    user_id    = colander.SchemaNode(
                    colander.Integer(),
                    oid="user_id",
                    missing=colander.drop)
    user_nm    = colander.SchemaNode(
                    colander.String(),
                    missing=colander.drop,
                    oid="user_nm",
                    title="User")
    email      = colander.SchemaNode(
                    colander.String(),
                    oid="email",
                    #missing=colander.drop,
                    title="E-Mail")
    handphone  = colander.SchemaNode(
                    colander.String(),
                    oid="handphone",
                    #missing=colander.drop,
                    title="Handphone")
    alamat     = colander.SchemaNode(
                    colander.String(),
                    #missing=colander.drop,
                    oid="alamat",
                    title="Alamat")
                

class EditSchema(AddSchema):
    id = colander.SchemaNode(colander.String(),
            missing=colander.drop,
            widget=widget.HiddenWidget(readonly=True))
                    

def get_form(request, class_form):
    schema = class_form(validator=form_validator)
    schema = schema.bind()
    schema.request = request
    return Form(schema, buttons=('save','cancel'))
    
def save(values, user, row=None):
    if not row:
        row = Pegawai()
        row.create_uid = user.id
        row.created    = datetime.now()
    else:
        row.update_uid = user.id
        row.updated    = datetime.now()
    row.from_dict(values)
    if not row.user_id or row.user_id==0 or row.user_id=='0':
        a = DBSession.query(User).filter(User.email==row.email).first()    
        if a:
            row.user_id = a.id
        else:
            row.user_id = None
        
    DBSession.add(row)
    DBSession.flush()
    return row
    
def save_request(values, request, row=None):
    if 'id' in request.matchdict:
        values['id'] = request.matchdict['id']
    row = save(values, request.user, row)
    request.session.flash('Pegawai %s sudah disimpan.' % row.nama)
        
def route_list(request):
    return HTTPFound(location=request.route_url('notadinas-pegawai'))
    
def session_failed(request, session_name):
    r = dict(form=request.session[session_name])
    del request.session[session_name]
    return r
    
@view_config(route_name='notadinas-pegawai-add', renderer='templates/pegawai/add.pt',
             permission='notadinas-pegawai-add')
def view_add(request):
    form = get_form(request, AddSchema)
    if request.POST:
        if 'simpan' in request.POST:
            controls = request.POST.items()
            try:
                c = form.validate(controls)
            except ValidationFailure, e:
                #request.session[SESS_ADD_FAILED] = e.render()  
                return dict(form=form)				
                return HTTPFound(location=request.route_url('notadinas-pegawai-add'))
            save_request(dict(controls), request)
        return route_list(request)
    elif SESS_ADD_FAILED in request.session:
        return session_failed(request, SESS_ADD_FAILED)
    return dict(form=form)

########
# Edit #
########
def query_id(request):
    return DBSession.query(Pegawai).filter_by(id=request.matchdict['id'])
    
def id_not_found(request):    
    msg = 'Pegawai ID %s not found.' % request.matchdict['id']
    request.session.flash(msg, 'error')
    return route_list(request)

@view_config(route_name='notadinas-pegawai-edit', renderer='templates/pegawai/edit.pt',
             permission='notadinas-pegawai-edit')
def view_edit(request):
    row = query_id(request).first()
    if not row:
        return id_not_found(request)
    form = get_form(request, EditSchema)
    if request.POST:
        if 'simpan' in request.POST:
            controls = request.POST.items()
            try:
                c = form.validate(controls)
            except ValidationFailure, e:
                return dict(form=form)
            save_request(dict(controls), request, row)
        return route_list(request)
    elif SESS_EDIT_FAILED in request.session:
        return session_failed(request, SESS_EDIT_FAILED)
    values = row.to_dict()
    values['unit_nm']    = row and row.units.nama      or ''
    values['jabatan_nm'] = row and row.jabatans.nama   or ''
	
    #values['user_id']    = row and row.user_id         or None
    if values['user_id']!=None:
        a = DBSession.query(User).filter(User.id==values['user_id']).first()
        if a:
            values['user_nm'] = a.user_name
        else:
            values['user_nm'] = ''
    else:
        values['user_nm'] = ''
        values['user_id'] = 0
			
    form.set_appstruct(values)
    return dict(form=form)

##########
# Delete #
##########    
@view_config(route_name='notadinas-pegawai-delete', renderer='templates/pegawai/delete.pt',
             permission='notadinas-pegawai-delete')
def view_delete(request):
    q = query_id(request)
    row = q.first()
    if not row:
        return id_not_found(request)
    form = Form(colander.Schema(), buttons=('hapus','batal'))
    if request.POST:
        if 'hapus' in request.POST:
            msg = 'Pegawai ID %d %s sudah dihapus.' % (row.id, row.nama)
            q.delete()
            DBSession.flush()
            request.session.flash(msg)
        return route_list(request)
    return dict(row=row, form=form.render())