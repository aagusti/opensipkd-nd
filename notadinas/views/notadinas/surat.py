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
    Surat, SuratDetail, PenerimaSurat, Disposisi, DisposisiComment, Job, Pegawai
    )
from ...models.pemda import (
    Unit, Urusan
    )
from datatables import ColumnDT, DataTables
from datetime import datetime,date
from ...tools import create_now, UploadFiles, get_settings, file_type
from ...views.base_view import _DTstrftime

SESS_ADD_FAILED = 'surat add failed'
SESS_EDIT_FAILED = 'surat edit failed'
 
# Jenis 
def deferred_jenis(node, kw):
    values = kw.get('is_jenis', [])
    return widget.SelectWidget(values=values)
    
IS_JENIS = (
    ('1', 'Surat Masuk'),
    ('2', 'Surat Keluar'),
    )
	
# Sifat 
def deferred_sifat(node, kw):
    values = kw.get('is_sifat', [])
    return widget.SelectWidget(values=values)
    
IS_SIFAT = (
    ('0', 'Biasa'),
    ('1', 'Segera'),
    ('2', 'Sangat Segera'),
    ('3', 'Rahasia'),
    )
	
# Status 
def deferred_status(node, kw):
    values = kw.get('is_status', [])
    return widget.SelectWidget(values=values)
    
IS_STATUS = (
    ('0', 'Masuk'),
    ('1', 'Keluar'),
    ('2', 'Diteruskan'),
    )
	
########                    
# List #
########    
@view_config(route_name='notadinas-surat', renderer='templates/surat/list.pt',
             permission='notadinas-surat')
def view_list(request):
    return dict(project='Notadinas')
    
##########                    
# Action #
##########    
@view_config(route_name='notadinas-surat-act', renderer='json',
             permission='notadinas-surat-act')
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
            columns.append(ColumnDT('from_to'))
            columns.append(ColumnDT('nama'))
            columns.append(ColumnDT('tanggal_surat', filter=_DTstrftime))
            columns.append(ColumnDT('tanggal_terima', filter=_DTstrftime))
            columns.append(ColumnDT('sifat'))
            columns.append(ColumnDT('status'))
            columns.append(ColumnDT('agenda'))
            
            query = DBSession.query(Surat)
            rowTable = DataTables(req, Surat, query, columns)
            return rowTable.output_result()
        else:
            columns = []
            columns.append(ColumnDT('id'))
            columns.append(ColumnDT('from_to'))
            columns.append(ColumnDT('nama'))
            columns.append(ColumnDT('tanggal_surat', filter=_DTstrftime))
            columns.append(ColumnDT('tanggal_terima', filter=_DTstrftime))
            columns.append(ColumnDT('sifat'))
            columns.append(ColumnDT('status'))
            columns.append(ColumnDT('agenda'))
            
            query = DBSession.query(Surat
                            ).filter(Surat.create_uid==u)
            rowTable = DataTables(req, Surat, query, columns)
            return rowTable.output_result()
    
    elif url_dict['act']=='grid1':
        cari = 'cari' in params and params['cari'] or ''
        u = req.user.id
        if u == 1:
            columns = []
            columns.append(ColumnDT('id'))
            columns.append(ColumnDT('from_to'))
            columns.append(ColumnDT('nama'))
            columns.append(ColumnDT('tanggal_surat', filter=_DTstrftime))
            columns.append(ColumnDT('tanggal_terima', filter=_DTstrftime))
            columns.append(ColumnDT('sifat'))
            columns.append(ColumnDT('status'))
            columns.append(ColumnDT('agenda'))
            
            query = DBSession.query(Surat
                            ).filter(or_(Surat.nama.ilike('%%%s%%' % cari),
                                         Surat.kode.ilike('%%%s%%' % cari),
                                         Surat.from_to.ilike('%%%s%%' % cari),))
            rowTable = DataTables(req, Surat, query, columns)
            return rowTable.output_result() 
        else:
            columns = []
            columns.append(ColumnDT('id'))
            columns.append(ColumnDT('from_to'))
            columns.append(ColumnDT('nama'))
            columns.append(ColumnDT('tanggal_surat', filter=_DTstrftime))
            columns.append(ColumnDT('tanggal_terima', filter=_DTstrftime))
            columns.append(ColumnDT('sifat'))
            columns.append(ColumnDT('status'))
            columns.append(ColumnDT('agenda'))
            
            query = DBSession.query(Surat
                            ).filter(Surat.create_uid==u,
                                     or_(Surat.nama.ilike('%%%s%%' % cari),
                                         Surat.kode.ilike('%%%s%%' % cari),
                                         Surat.from_to.ilike('%%%s%%' % cari),))
            rowTable = DataTables(req, Surat, query, columns)
            return rowTable.output_result() 
        
    elif url_dict['act']=='hon_disposisi':
        term = 'term' in params and params['term'] or '' 
        rows = DBSession.query(Surat.id, 
                               Surat.kode, 
                               Surat.nama, 
                               Surat.no_surat, 
                               Surat.from_to, 
                               Surat.tanggal_surat, 
                               Surat.tanggal_terima
                  ).filter(Surat.nama.ilike('%%%s%%' % term) 
                  ).all()
        r = []
        for k in rows:
            d={}
            d['id']      = k[0]
            d['value']   = k[2]
            d['kode']    = k[1]
            d['nama']    = k[2]
            d['no']      = k[3]
            d['from']    = k[4]
            d['tgl']     = "%s" % k[5]
            d['tgl_t']   = "%s" % k[6]
            r.append(d)
        return r    
        
    elif url_dict['act']=='hok_disposisi':
        term = 'term' in params and params['term'] or '' 
        rows = DBSession.query(Surat.id, 
                               Surat.kode, 
                               Surat.nama, 
                               Surat.no_surat, 
                               Surat.from_to, 
                               Surat.tanggal_surat, 
                               Surat.tanggal_terima
                  ).filter(Surat.no_surat.ilike('%%%s%%' % term) 
                  ).all()
        r = []
        for k in rows:
            d={}
            d['id']      = k[0]
            d['value']   = k[3]
            d['kode']    = k[1]
            d['nama']    = k[2]
            d['no']      = k[3]
            d['from']    = k[4]
            d['tgl']     = "%s" % k[5]
            d['tgl_t']   = "%s" % k[6]
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
                
    if 'id' in form.request.matchdict:
        uid = form.request.matchdict['id']
        q = DBSession.query(Surat).filter_by(id=uid)
        produk = q.first()
    else:
        produk = None
        
    q = DBSession.query(Surat).filter_by(kode=value['kode'])
    found = q.first()
    if produk:
        if found and found.id != produk.id:
            err_kode()
    elif found:
        err_kode()
            
tmpstore = FileUploadTempStore()  				

auto_pg_nm = widget.AutocompleteInputWidget(
    size=60,
    values = '/notadinas/pegawai/hon_pegawai_penerima/act',
    min_length=1,
    limit=10)
        
class Uploads(colander.SequenceSchema):
    upload  = colander.SchemaNode(
                FileData(),
                widget=widget.FileUploadWidget(tmpstore),
                validator = None,
                title="Upload File"
                )
                     
class Penerima(colander.SequenceSchema):
    pegawai    = colander.SchemaNode(
                    colander.String(),
                    widget=auto_pg_nm,
                    oid = "pegawai",
                    title="Penerima"
                    )

class AddSchema(colander.Schema):
    kode           = colander.SchemaNode(
                        colander.String(),
                        oid = "kode",
                        title = "Kode",)
    nama           = colander.SchemaNode(
                        colander.String(),
                        oid = "nama",
                        title = "Perihal",)
    from_to        = colander.SchemaNode(
                        colander.String(),
                        oid = "from_to",
                        title = "Dari/Untuk",)
    no_surat       = colander.SchemaNode(
                        colander.String(),
                        oid = "no_surat",
                        title = "No.Surat",)
    tanggal_surat  = colander.SchemaNode(
                        colander.Date(),
                        oid="tanggal_surat",
                        title="Tgl.Surat")
    tanggal_terima = colander.SchemaNode(
                        colander.Date(),
                        oid="tanggal_terima",
                        title="Tgl.Terima")
    indeks         = colander.SchemaNode(
                        colander.String(),
                        missing=colander.drop,
                        oid = "indeks",
                        title = "Indeks",)
    agenda         = colander.SchemaNode(
                        colander.String(),
                        missing=colander.drop,
                        oid = "agenda",
                        title = "Agenda",)
    lampiran       = colander.SchemaNode(
                        colander.String(),
                        missing=colander.drop,
                        oid = "lampiran",
                        title = "Lampiran",)
    jenis          = colander.SchemaNode(
                        colander.String(),
                        missing=colander.drop,
                        widget=widget.SelectWidget(values=IS_JENIS),
                        oid="jenis",
                        title="Jenis")
    sifat          = colander.SchemaNode(
                        colander.String(),
                        missing=colander.drop,
                        widget=widget.SelectWidget(values=IS_SIFAT),
                        oid="sifat",
                        title="Sifat")
    status         = colander.SchemaNode(
                        colander.String(),
                        missing=colander.drop,
                        widget=widget.SelectWidget(values=IS_STATUS),
                        oid="status",
                        title="Status")
    uploads        = Uploads()
    penerima       = Penerima()
    
    
class EditSchema(AddSchema):
    id             = colander.SchemaNode(
                        colander.Integer(),
                        oid="id")
                    

def get_form(request, class_form):
    schema = class_form(validator=form_validator)
    schema = schema.bind(is_jenis=IS_JENIS,is_sifat=IS_SIFAT,is_status=IS_STATUS)
    schema.request = request
    return Form(schema, buttons=('simpan','batal'))
    
def save(values, user, row=None):
    if not row:
        row = Surat()
        row.create_uid = user.id
        row.created    = datetime.now()
    else:
        row.update_uid = user.id
        row.updated    = datetime.now()
    row.from_dict(values)
    if row.tanggal_surat=='':
        row.tanggal_surat = None
    if row.tanggal_terima=='':
        row.tanggal_terima = None
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
    
class DbUpload(UploadFiles):
    def __init__(self):
        settings = get_settings()
        dir_path = os.path.realpath(settings['static_files'])
        UploadFiles.__init__(self, dir_path)
        
    def save(self, request, names, surat_id):
        fileslist = request.POST.getall(names)
        for f in fileslist:
            fullpath = UploadFiles.save(self, f)
            msg = 'File {fullpath} sudah disimpan.'
            msg = msg.format(fullpath=fullpath)
            
            row = SuratDetail()
            row.path     = fullpath[len(self.dir_path)+1:]
            row.name     = f.filename
            row.size     = os.stat(fullpath).st_size
            row.mime     = file_type(fullpath)
            row.user_id  = request.user.id
            row.surat_id = surat_id
            
            DBSession.add(row)
            DBSession.flush()  

class DbPenerima(Penerima):
    def __init__(self):
        settings = get_settings()
        
    def save(self, request, names, surat_id):
        plist = request.POST.getall(names)
        for f in plist:
            a = f
            print '-------------------nama-------------------',f
            # Mengambil ID dari nama yang dikirim #
            b = DBSession.query(Pegawai.id
                        ).filter(Pegawai.nama==a 
                        ).first()
            print '-------------------id---------------------',b  
            
            # Mengecek pegawai ditakutkan telah terpakai #            
            c = DBSession.query(PenerimaSurat
                        ).filter(PenerimaSurat.surat_id==surat_id,
                                 PenerimaSurat.pegawai_id==b 
                        ).first()
            print '-------------------terpakai---------------',c 
            
            msg = 'Maaf penerima %s sudah terdaftar dalam list.' % a
            if not c: 
                row = PenerimaSurat()
                row.surat_id    = surat_id
                row.pegawai_id  = b
                row.user_id     = request.user.id
                row.tanggal     = datetime.now()
                row.disabled    = 0
                
                DBSession.add(row)
                DBSession.flush()                    
            
def save_request(values, request, row=None):
    if 'id' in request.matchdict:
        values['id'] = request.matchdict['id']
    row = save(values, request.user, row)
    if row:
        dbu = DbUpload()
        dbu.save(request, 'upload', row.id)    
        
        dbu = DbPenerima()
        dbu.save(request, 'pegawai', row.id)   
        
        request.session.flash('Surat perihal %s sudah disimpan atau dikirim.' % row.nama)   
    return row
	
def route_list(request):
    return HTTPFound(location=request.route_url('notadinas-surat'))
    
def session_failed(request, session_name):
    r = dict(form=request.session[session_name])
    del request.session[session_name]
    return r
    
@view_config(route_name='notadinas-surat-add', renderer='templates/surat/add.pt',
             permission='notadinas-surat-add')
def view_add(request):
    form = get_form(request, AddSchema)
    print '...........--------form-------...........',form
    if request.POST:
        #if 'simpan' in request.POST:
        controls = request.POST.items()
        print '...........-----controls------...........',controls

        #controls_dicted = dict(controls)
        #try:
        #    c = form.validate(controls)
        #except ValidationFailure, e:
        #    return dict(form=form)
        row = save_request(dict(controls), request)		
        print '...........--------row--------...........',row	
        return HTTPFound(location=request.route_url('notadinas-surat-edit',id=row.id))
        return route_list(request)
    elif SESS_ADD_FAILED in request.session:
        return session_failed(request, SESS_ADD_FAILED)
    return dict(form=form)

########
# Edit #
########
def query_id(request):
    return DBSession.query(Surat).filter_by(id=request.matchdict['id'])
    
def id_not_found(request):    
    msg = 'Surat ID %s not found.' % request.matchdict['id']
    request.session.flash(msg, 'error')
    return route_list(request)

@view_config(route_name='notadinas-surat-edit', renderer='templates/surat/edit.pt',
             permission='notadinas-surat-edit')
def view_edit(request):
    row = query_id(request).first()
	
    if not row:
        return id_not_found(request)
		
    form = get_form(request, EditSchema)
    if request.POST:
        if 'simpan' in request.POST:
            controls = request.POST.items()
            row = save_request(dict(controls), request, row)
            
            # Array disposisi sesuai penerima #
            jui   = row.id
            rows = DBSession.query(Pegawai.user_id.label('penerima1'),
                                ).filter(PenerimaSurat.surat_id==jui,
                                         PenerimaSurat.pegawai_id==Pegawai.id
                                ).all()
            for row in rows:   
                c = DBSession.query(Disposisi.id
                            ).filter(Disposisi.surat_id==jui,
                                     Disposisi.to_uid==row.penerima1
                            ).first()
                print '-----------array disposisi terpakai-------',c 
                if not c:            
                    ji1 = Disposisi()
                    ji1.surat_id      = jui
                    ji1.from_uid      = request.user.id
                    ji1.to_uid        = row.penerima1
                    ji1.tanggal       = datetime.now()
                    ji1.notes         = ""
                    ji1.job_id        = None
                    ji1.need_feedback = 0
                    ji1.date_feedback = None
                    ji1.status        = 0
                    ji1.dis_id        = 0
                    DBSession.add(ji1)
                    DBSession.flush()
                    
        return route_list(request)
    elif SESS_EDIT_FAILED in request.session:
        return session_failed(request, SESS_EDIT_FAILED)
    values = row.to_dict()
    form.set_appstruct(values)
    return dict(form=form)

##########
# Delete #
##########    
@view_config(route_name='notadinas-surat-delete', renderer='templates/surat/delete.pt',
             permission='notadinas-surat-delete')
def view_delete(request):
    q = query_id(request)
    row = q.first()
    a   = row.id
	
    if not row:
        return id_not_found(request)
		
    # Seleksi untuk mengecek file
    i = DBSession.query(SuratDetail).filter(SuratDetail.surat_id==a).first()
    if i:
        request.session.flash('Hapus dahulu file surat.', 'error')
        return route_list(request)
		
    # Seleksi untuk mengecek penerima
    a = DBSession.query(PenerimaSurat).filter(PenerimaSurat.surat_id==a).first()
    if a:
        request.session.flash('Hapus dahulu penerima surat.', 'error')
        return route_list(request)
		
    form = Form(colander.Schema(), buttons=('hapus','batal'))
    if request.POST:
        if 'hapus' in request.POST:
            msg = 'Surat ID %d sudah dihapus.' % (row.id)
            q.delete()
            DBSession.flush()
            request.session.flash(msg)
        return route_list(request)
    return dict(row=row, form=form.render())
