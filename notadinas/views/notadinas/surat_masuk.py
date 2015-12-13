import os
from email.utils import parseaddr
from sqlalchemy import not_, func, cast, BigInteger, String, or_
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
    FileData,
    )
from deform.interfaces import FileUploadTempStore
from ...models import(
    DBSession,
    )
from ...models.notadinas import (
    Surat, SuratDetail, PenerimaSurat, Disposisi, DisposisiComment, PenerimaDisposisi, Job, Pegawai
    )
from ...models.pemda import (
    Unit, Urusan
    )
from datatables import ColumnDT, DataTables
from datetime import datetime,date
from ...tools import create_now, UploadFiles, get_settings, file_type
from ...views.base_view import _DTstrftime,_number_format

SESS_ADD_FAILED = 'surat add failed'
SESS_EDIT_FAILED = 'surat edit failed'
 
# Need Feedback 
def deferred_feedback(node, kw):
    values = kw.get('is_feedback', [])
    return widget.SelectWidget(values=values)
    
IS_FEEDBACK = (
    ('0', 'Tidak'),
    ('1', 'Ya'),
    )
	
# Status 
def deferred_status(node, kw):
    values = kw.get('is_status', [])
    return widget.SelectWidget(values=values)
    
IS_STATUS = (
    ('0', 'Unread'),
    ('1', 'Read'),
    ('2', 'Diteruskan'),
    )
	
########                    
# List #
########    
@view_config(route_name='notadinas-surat-inbox', renderer='templates/surat_masuk/list.pt',
             permission='notadinas-surat-inbox')
def view_list(request):
    return dict(project='Notadinas')
    
##########                    
# Action #
##########    
@view_config(route_name='notadinas-surat-inbox-act', renderer='json',
             permission='notadinas-surat-inbox-act')
def surat_act(request):
    ses = request.session
    req = request
    params   = req.params
    url_dict = req.matchdict
    
    if url_dict['act']=='grid':
        u = req.user.id
        if u == 1:
            columns = []
            columns.append(ColumnDT('id'))
            columns.append(ColumnDT('surats.from_to'))
            columns.append(ColumnDT('surats.nama'))
            columns.append(ColumnDT('tanggal', filter=_DTstrftime))
            columns.append(ColumnDT('need_feedback'))
            columns.append(ColumnDT('date_feedback', filter=_DTstrftime))
            columns.append(ColumnDT('status'))
            
            query = DBSession.query(Disposisi
                            ).join(Surat
                            ).filter(Disposisi.surat_id == Surat.id,
                                     Disposisi.status   != 2,
                            )
            rowTable = DataTables(req, Disposisi, query, columns)
            return rowTable.output_result()
        else:
            columns = []
            columns.append(ColumnDT('id'))
            columns.append(ColumnDT('surats.from_to'))
            columns.append(ColumnDT('surats.nama'))
            columns.append(ColumnDT('tanggal', filter=_DTstrftime))
            columns.append(ColumnDT('need_feedback'))
            columns.append(ColumnDT('date_feedback', filter=_DTstrftime))
            columns.append(ColumnDT('status'))
            
            query = DBSession.query(Disposisi
                            ).join(Surat
                            ).filter(Disposisi.surat_id == Surat.id,
                                     Disposisi.to_uid   == req.user.id
                            )
            rowTable = DataTables(req, Disposisi, query, columns)
            return rowTable.output_result()
    
    elif url_dict['act']=='grid1':
        cari = 'cari' in params and params['cari'] or ''
        u = req.user.id
        if u == 1:
            columns = []
            columns.append(ColumnDT('id'))
            columns.append(ColumnDT('surats.from_to'))
            columns.append(ColumnDT('surats.nama'))
            columns.append(ColumnDT('tanggal', filter=_DTstrftime))
            columns.append(ColumnDT('need_feedback'))
            columns.append(ColumnDT('date_feedback', filter=_DTstrftime))
            columns.append(ColumnDT('status'))
            
            query = DBSession.query(Disposisi
                            ).join(Surat
                            ).filter(Disposisi.surat_id == Surat.id,
                                     Disposisi.status   != 2,
                                     or_(Surat.nama.ilike('%%%s%%' % cari),
                                         Surat.from_to.ilike('%%%s%%' % cari))
                            )
            rowTable = DataTables(req, Disposisi, query, columns)
            return rowTable.output_result()
        else:
            columns = []
            columns.append(ColumnDT('id'))
            columns.append(ColumnDT('surats.from_to'))
            columns.append(ColumnDT('surats.nama'))
            columns.append(ColumnDT('tanggal', filter=_DTstrftime))
            columns.append(ColumnDT('need_feedback'))
            columns.append(ColumnDT('date_feedback', filter=_DTstrftime))
            columns.append(ColumnDT('status'))
            
            query = DBSession.query(Disposisi
                            ).join(Surat
                            ).filter(Disposisi.surat_id == Surat.id,
                                     Disposisi.to_uid   == req.user.id,
                                     or_(Surat.nama.ilike('%%%s%%' % cari),
                                         Surat.from_to.ilike('%%%s%%' % cari))
                            )
            rowTable = DataTables(req, Disposisi, query, columns)
            return rowTable.output_result()
    
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
        q = DBSession.query(Disposisi).filter_by(id=uid)
        job = q.first()
    else:
        job = None
        
tmpstore = FileUploadTempStore()  	
     
auto_pg_nm = widget.AutocompleteInputWidget(
    size=60,
    values = '/notadinas/pegawai/hon_pegawai_penerima/act',
    min_length=1,
    limit=10)
    
class Penerima(colander.SequenceSchema):
    pegawai    = colander.SchemaNode(
                    colander.String(),
                    widget=auto_pg_nm,
                    oid = "pegawai",
                    title="Penerima"
                    )
                    
class AddSchema(colander.Schema):
    surat_id       = colander.SchemaNode(
                        colander.Integer(),
                        oid = "surat_id")
    surat_no       = colander.SchemaNode(
                        colander.String(),
                        oid = "surat_no",
                        title = "Surat")
    surat_nm       = colander.SchemaNode(
                        colander.String(),
                        oid = "surat_nm",
                        title = "Perihal")
    surat_ft       = colander.SchemaNode(
                        colander.String(),
                        oid = "surat_ft",
                        title = "Dari/Untuk",)
    surat_tgl      = colander.SchemaNode(
                        colander.Date(),
                        oid="surat_tgl",
                        title="Tgl.Surat")
    surat_tgl1     = colander.SchemaNode(
                        colander.Date(),
                        oid="surat_tgl1",
                        title="Tgl.Terima")
    job_id         = colander.SchemaNode(
                        colander.Integer(),
                        missing=colander.drop,
                        oid = "job_id")
    job_nm         = colander.SchemaNode(
                        colander.String(),
                        missing=colander.drop,
                        oid = "job_nm",
                        title = "Pekerjaan")
    tanggal        = colander.SchemaNode(
                        colander.Date(),
                        oid="tanggal",
                        title="Tanggal")
    notes          = colander.SchemaNode(
                        colander.String(),
                        missing=colander.drop,
                        oid = "notes",
                        title = "Catatan",)
    need_feedback  = colander.SchemaNode(
                        colander.String(),
                        missing=colander.drop,
                        widget=widget.SelectWidget(values=IS_FEEDBACK),
                        oid="need_feedback",
                        title="Balas")
    date_feedback  = colander.SchemaNode(
                        colander.Date(),
                        missing=colander.drop,
                        oid="date_feedback",
                        title="Tgl.Balas")
    status         = colander.SchemaNode(
                        colander.String(),
                        missing=colander.drop,
                        widget=widget.SelectWidget(values=IS_STATUS),
                        oid="status",
                        title="Status")
    penerima       = Penerima()
                

class EditSchema(AddSchema):
    id        = colander.SchemaNode(
                   colander.Integer(),
                   oid="id")
                    
def get_form(request, class_form):
    schema = class_form(validator=form_validator)
    schema = schema.bind(is_feedback=IS_FEEDBACK,is_status=IS_STATUS)
    schema.request = request
    return Form(schema, buttons=('simpan','batal'))
    
def save(values, user, row=None):
    if not row:
        row = Disposisi()
        row.create_uid = user.id
        row.created    = datetime.now()
    else:
        row.update_uid = user.id
        row.updated    = datetime.now()
    row.from_dict(values)
    
    # Seleksi status #
    j='1'
    j1 = row.need_feedback
    if j1 != j:
        row.date_feedback = None
    if row.job_id == '':
        row.job_id = None     
        
    DBSession.add(row)
    DBSession.flush()
    return row
    
def get_seq(controls, name):
    start = False
    key_value = ':'.join([name, 'sequence'])
    r = []
    for key, value in controls:
        if key == '__start__' and value == key_value:
            start = True
            continue
        if key == '__end__' and value == key_value:
            start = False
        if start:
            r.append(value)
    return r
    
class DbPenerima(Penerima):
    def __init__(self):
        settings = get_settings()
        
    def save(self, request, names, disposisi_id):
        plist = request.POST.getall(names)
        for f in plist:
            a = f
            print '-------------------nama-------------------',f
            # Mengambil ID dari nama yang dikirim #
            b = DBSession.query(Pegawai.id
                        ).filter(Pegawai.nama==a 
                        ).first()
            print '----------------id pegawai----------------',b  
            
            # Mengambil ID Surat dari Disposisi yang sama #            
            d = DBSession.query(Disposisi.surat_id
                        ).filter(Disposisi.id==disposisi_id, 
                        ).first()
            print '-------------------id surat---------------',d 
            
            # Mengecek pegawai ditakutkan telah terpakai #            
            c = DBSession.query(PenerimaDisposisi
                        ).filter(PenerimaDisposisi.disposisi_id==Disposisi.id,
                                 Disposisi.surat_id==d,
                                 PenerimaDisposisi.pegawai_id==b 
                        ).first()
            print '-------------pegawai terpakai-------------',c 
            
            msg = 'Maaf penerima %s sudah terdaftar dalam list.' % a
            if not c: 
                row = PenerimaDisposisi()
                row.disposisi_id = disposisi_id
                row.pegawai_id   = b
                row.user_id      = request.user.id
                row.tanggal      = datetime.now()
                row.disabled     = 0
                
                DBSession.add(row)
                DBSession.flush()          
                
def save_request(values, request, row=None):
    if 'id' in request.matchdict:
        values['id'] = request.matchdict['id']
    row = save(values, request.user, row)
    if row:
        dbu = DbPenerima()
        dbu.save(request, 'pegawai', row.id)   
        
        request.session.flash('Surat masuk id %s sudah disimpan.' % row.id)   
    return row
	
def route_list(request):
    return HTTPFound(location=request.route_url('notadinas-surat-inbox'))
    
def session_failed(request, session_name):
    r = dict(form=request.session[session_name])
    del request.session[session_name]
    return r
    
@view_config(route_name='notadinas-surat-inbox-add', renderer='templates/surat_masuk/add.pt',
             permission='notadinas-surat-inbox-add')
def view_add(request):
    form = get_form(request, AddSchema)
    if request.POST:
        if 'simpan' in request.POST:
            controls = request.POST.items()
            controls_dicted = dict(controls)
            try:
                c = form.validate(controls)
            except ValidationFailure, e:
                return dict(form=form)
            row = save_request(controls_dicted, request)	
            print '......................---------------...........',row			
            return HTTPFound(location=request.route_url('notadinas-surat-inbox-edit',id=row.id))
        return route_list(request)
    elif SESS_ADD_FAILED in request.session:
        return session_failed(request, SESS_ADD_FAILED)
    return dict(form=form)

########
# Edit #
########
def query_id(request):
    return DBSession.query(Disposisi).filter_by(id=request.matchdict['id'])
    
def id_not_found(request):    
    msg = 'Surat masuk ID %s not found.' % request.matchdict['id']
    request.session.flash(msg, 'error')
    return route_list(request)
    
def save_request2(request, r=None):
    r = Disposisi()
    return r
    
@view_config(route_name='notadinas-surat-inbox-edit', renderer='templates/surat_masuk/edit.pt',
             permission='notadinas-surat-inbox-edit')
def view_edit(request):
    row = query_id(request).first()
    s = row.id
    st= row.status
    
    if not row:
        return id_not_found(request)
        
	#Update status Read pada Disposisi
    r = DBSession.query(Disposisi).filter(Disposisi.id==s).first()
    if st == 2:
        r.status = 2
    else:
        r.status = 1
    save_request2(request, r)
            
    form = get_form(request, EditSchema)
    if request.POST:
        if 'simpan' in request.POST:
            controls = request.POST.items()
            row = save_request(dict(controls), request, row)
            
            # Array disposisi sesuai penerima #
            jui  = row.id
            js   = row.surat_id
            jn   = row.notes         
            jj   = row.job_id        
            jnf  = row.need_feedback 
            jdf  = row.date_feedback
                 
            rows = DBSession.query(Pegawai.user_id.label('penerima1'),
                                ).filter(PenerimaDisposisi.disposisi_id==jui,
                                         PenerimaDisposisi.pegawai_id==Pegawai.id
                                ).all()
            for row in rows:                
                c = DBSession.query(Disposisi.id
                            ).filter(Disposisi.surat_id==js,
                                     Disposisi.to_uid==row.penerima1
                            ).first()
                print '-----------araay disposisi terpakai-------',c 
                if not c:
                    ji1 = Disposisi()
                    ji1.surat_id      = js
                    ji1.from_uid      = request.user.id
                    ji1.to_uid        = row.penerima1
                    ji1.tanggal       = datetime.now()
                    ji1.notes         = jn
                    ji1.job_id        = jj
                    ji1.need_feedback = jnf
                    ji1.date_feedback = jdf
                    ji1.status        = 0
                    ji1.dis_id        = jui
                    DBSession.add(ji1)
                    DBSession.flush()
                    
        return route_list(request)
    elif SESS_EDIT_FAILED in request.session:
        return session_failed(request, SESS_EDIT_FAILED)
    values = row.to_dict()
    values['surat_no']   = row and row.surats.no_surat       or ''
    values['surat_nm']   = row and row.surats.nama           or ''
    values['surat_ft']   = row and row.surats.from_to        or ''
    values['surat_tgl']  = row and row.surats.tanggal_surat  or ''
    values['surat_tgl1'] = row and row.surats.tanggal_terima or ''
    
    if values['job_id']!=None:
        a = DBSession.query(Job).filter(Job.id==values['job_id']).first()
        if a:
            values['job_nm'] = a.nama
        else:
            values['job_nm'] = ''
    else:
        values['job_nm'] = ''
        values['job_id'] = 0
        
    form.set_appstruct(values)
    return dict(form=form)
   
@view_config(route_name='notadinas-surat-inbox-reply', renderer='templates/surat_masuk/reply.pt',
             permission='notadinas-surat-inbox-reply')
def view_reply(request):
    row = query_id(request).first()
    s = row.id
    st= row.status
    
    if not row:
        return id_not_found(request)
        
	#Update status Read pada Disposisi
    r = DBSession.query(Disposisi).filter(Disposisi.id==s).first()
    if st == 2:
        r.status = 2
    else:
        r.status = 1
    save_request2(request, r)
            
    form = get_form(request, EditSchema)
    if request.POST:
        if 'simpan' in request.POST:
            controls = request.POST.items()
            row = save_request(dict(controls), request, row)
        return route_list(request)
    elif SESS_EDIT_FAILED in request.session:
        return session_failed(request, SESS_EDIT_FAILED)
    values = row.to_dict()
    values['surat_no']   = row and row.surats.no_surat       or ''
    values['surat_nm']   = row and row.surats.nama           or ''
    values['surat_ft']   = row and row.surats.from_to        or ''
    values['surat_tgl']  = row and row.surats.tanggal_surat  or ''
    values['surat_tgl1'] = row and row.surats.tanggal_terima or ''
    
    if values['job_id']!=None:
        a = DBSession.query(Job).filter(Job.id==values['job_id']).first()
        if a:
            values['job_nm'] = a.nama
        else:
            values['job_nm'] = ''
    else:
        values['job_nm'] = ''
        values['job_id'] = 0
        
    form.set_appstruct(values)
    return dict(form=form)
       
@view_config(route_name='notadinas-surat-inbox-forward', renderer='templates/surat_masuk/forward.pt',
             permission='notadinas-surat-inbox-forward')
def view_forward(request):
    row = query_id(request).first()
    s = row.id
    st= row.status
    
    if not row:
        return id_not_found(request)
        
	#Update status Read pada Disposisi
    r = DBSession.query(Disposisi).filter(Disposisi.id==s).first()
    if st == 2:
        r.status = 2
    else:
        r.status = 1
    save_request2(request, r)
            
    form = get_form(request, EditSchema)
    if request.POST:
        if 'simpan' in request.POST:
            controls = request.POST.items()
            row = save_request(dict(controls), request, row)
            
            # Array disposisi sesuai penerima #
            jui  = row.id
            js   = row.surat_id
            jn   = row.notes         
            jj   = row.job_id        
            jnf  = row.need_feedback 
            jdf  = row.date_feedback
                 
            rows = DBSession.query(Pegawai.user_id.label('penerima1'),
                                ).filter(PenerimaDisposisi.disposisi_id==jui,
                                         PenerimaDisposisi.pegawai_id==Pegawai.id
                                ).all()
            for row in rows:                
                c = DBSession.query(Disposisi.id
                            ).filter(Disposisi.surat_id==js,
                                     Disposisi.to_uid==row.penerima1
                            ).first()
                print '-----------araay disposisi terpakai-------',c 
                if not c:
                    ji1 = Disposisi()
                    ji1.surat_id      = js
                    ji1.from_uid      = request.user.id
                    ji1.to_uid        = row.penerima1
                    ji1.tanggal       = datetime.now()
                    ji1.notes         = jn
                    ji1.job_id        = jj
                    ji1.need_feedback = jnf
                    ji1.date_feedback = jdf
                    ji1.status        = 0
                    ji1.dis_id        = jui
                    DBSession.add(ji1)
                    DBSession.flush()
                    
        return route_list(request)
    elif SESS_EDIT_FAILED in request.session:
        return session_failed(request, SESS_EDIT_FAILED)
    values = row.to_dict()
    values['surat_no']   = row and row.surats.no_surat       or ''
    values['surat_nm']   = row and row.surats.nama           or ''
    values['surat_ft']   = row and row.surats.from_to        or ''
    values['surat_tgl']  = row and row.surats.tanggal_surat  or ''
    values['surat_tgl1'] = row and row.surats.tanggal_terima or ''
    
    if values['job_id']!=None:
        a = DBSession.query(Job).filter(Job.id==values['job_id']).first()
        if a:
            values['job_nm'] = a.nama
        else:
            values['job_nm'] = ''
    else:
        values['job_nm'] = ''
        values['job_id'] = 0
        
    form.set_appstruct(values)
    return dict(form=form)
    
##########
# Delete #
##########    
@view_config(route_name='notadinas-surat-inbox-delete', renderer='templates/surat_masuk/delete.pt',
             permission='notadinas-surat-inbox-delete')
def view_delete(request):
    q   = query_id(request)
    row = q.first()
    a   = row.id
	
    if not row:
        return id_not_found(request)
		
    # Seleksi untuk mengecek komentar
    i = DBSession.query(DisposisiComment).filter(DisposisiComment.disposisi_id==a).first()
    if i:
        request.session.flash('Hapus dahulu komentar pada surat masuk.', 'error')
        return route_list(request)
		
    # Seleksi untuk mengecek penerima
    b = DBSession.query(PenerimaDisposisi).filter(PenerimaDisposisi.disposisi_id==a).first()
    if b:
        request.session.flash('Hapus dahulu penerima.', 'error')
        return route_list(request)
        
    form = Form(colander.Schema(), buttons=('hapus','batal'))
    if request.POST:
        if 'hapus' in request.POST:
            msg = 'Surat masuk ID %d sudah dihapus.' % (row.id)
            q.delete()
            DBSession.flush()
            request.session.flash(msg)
        return route_list(request)
    return dict(row=row, form=form.render())
