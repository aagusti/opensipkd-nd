from email.utils import parseaddr
from sqlalchemy import not_, func, cast, BigInteger, String
from pyramid.view import (
    view_config,
    )
from pyramid.httpexceptions import (
    HTTPFound,
    )
import colander
from deform.interfaces import FileUploadTempStore
from deform import (
    Form,
    widget,
    ValidationFailure,
    FileData,
    )
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
from ...tools import create_now, get_settings, Upload, file_type
from ...views.base_view import _DTstrftime,_number_format

SESS_ADD_FAILED = 'Tambah surat-penerima2 gagal'
SESS_EDIT_FAILED = 'Edit surat-penerima2 gagal'

##########                    
# Action #
##########    
@view_config(route_name='notadinas-surat-penerima2-act', renderer='json',
             permission='notadinas-surat-penerima2-act')
def view_act(request):
    ses = request.session
    req = request
    params   = req.params
    url_dict = req.matchdict

    if url_dict['act']=='grid':
        # defining columns
        disposisi_id = url_dict['disposisi_id'].isdigit() and url_dict['disposisi_id'] or 0
        columns = []
        columns.append(ColumnDT('id'))
        columns.append(ColumnDT('disposisi_id'))
        columns.append(ColumnDT('pegawai_id'))
        columns.append(ColumnDT('pegawais.kode'))
        columns.append(ColumnDT('pegawais.nama'))
        columns.append(ColumnDT('tanggal', filter=_DTstrftime))
        columns.append(ColumnDT('disabled'))
        
        query = DBSession.query(PenerimaDisposisi).\
                          join(Disposisi, Pegawai).\
                          filter(PenerimaDisposisi.disposisi_id == disposisi_id,
                                 PenerimaDisposisi.pegawai_id   == Pegawai.id,
                          )
                          
        rowTable = DataTables(req, PenerimaDisposisi, query, columns)
        return rowTable.output_result()

    elif url_dict['act']=='file':
        disposisi_id = url_dict['disposisi_id'].isdigit() and url_dict['disposisi_id'] or 0
        columns = []
        columns.append(ColumnDT('id'))
        columns.append(ColumnDT('surat_id'))
        columns.append(ColumnDT('name'))
        columns.append(ColumnDT('size',filter=_number_format))
        columns.append(ColumnDT('path'))
        
        si = DBSession.query(Disposisi.surat_id).\
                          filter(Disposisi.id==disposisi_id,
                          )
        query = DBSession.query(SuratDetail).\
                          join(Surat).\
                          filter(SuratDetail.surat_id==si
                          )
                          
        rowTable = DataTables(req, SuratDetail, query, columns)
        return rowTable.output_result()
			
#######    
# Add #
#######
@view_config(route_name='notadinas-surat-penerima2-add', renderer='json',
             permission='notadinas-surat-penerima2-add')
def view_add(request):
    req = request
    ses = req.session
    params   = req.params
    url_dict = req.matchdict
    disposisi_id = 'disposisi_id' in url_dict and url_dict['disposisi_id'] or 0
    controls = dict(request.POST.items())
    
    disposisi_penerima_id = 'disposisi_penerima_id' in controls and controls['disposisi_penerima_id'] or 0
    pegawai_id            = 'pegawai_id'            in controls and controls['pegawai_id']            or 0
    #Cek dulu ada penyusup gak dengan mengecek sessionnya
    disposisi = DBSession.query(Disposisi)\
                     .filter(Disposisi.id==disposisi_id).first()
    if not disposisi:
        return {"success": False, 'msg':'Surat disposisi tidak ditemukan'}
    
    #Cek apakah penerima sudah terpakai apa belum
    penerima_disposisi = DBSession.query(PenerimaDisposisi)\
                              .filter(PenerimaDisposisi.disposisi_id == disposisi_id,
                                      PenerimaDisposisi.pegawai_id   == pegawai_id).first()
    if penerima_disposisi:
        return {"success": False, 'msg':'Penerima tidak boleh sama.'}
    
    #Cek lagi ditakutkan ada yang iseng inject script
    if disposisi_penerima_id:
        row = DBSession.query(PenerimaDisposisi)\
                  .join(Disposisi)\
                  .filter(PenerimaDisposisi.id==disposisi_penerima_id,
                          PenerimaDisposisi.disposisi_id==disposisi_id).first()
        if not row:
            return {"success": False, 'msg':'Penerima tidak ditemukan'}
    else:
        row = PenerimaDisposisi()
            
    row.disposisi_id = disposisi_id
    row.pegawai_id   = controls['pegawai_id']
    row.p_kode       = controls['p_kode']
    row.p_nama       = controls['p_nama']
    row.user_id      = req.user.id
    row.tanggal      = datetime.now()
    row.disabled     = 'disabled' in controls and 1 or 0
	
    DBSession.add(row)
    DBSession.flush()
	
    return {"success": True, 'id': row.id, "msg":'Success tambah Penerima Disposisi.'}


########
# Edit #
########
def route_list(request):
    return HTTPFound(location=request.route_url('notadinas-surat-inbox-edit',id=request.matchdict['disposisi_id']))
    
def query_id(request):
    return DBSession.query(PenerimaDisposisi).filter(PenerimaDisposisi.id==request.matchdict['id'],
                                                     PenerimaDisposisi.disposisi_id==request.matchdict['disposisi_id'])
    
def id_not_found(request):    
    msg = 'Disposisi ID %s not found.' % request.matchdict['id']
    request.session.flash(msg, 'error')
    return route_list(request)

##########
# Delete #
##########    
@view_config(route_name='notadinas-surat-penerima2-delete', renderer='json',
             permission='notadinas-surat-penerima2-delete')
def view_delete(request):
    q = query_id(request)
    row = q.first()
    a = row.user_id
    b = request.user.id
    
    if not row:
        return {'success':False, "msg":self.id_not_found()}
        
    if a!=b:
        request.session.flash('Maaf datanya tidak bisa dihapus.', 'error')
        return route_list(request)
        
    msg = 'Data sudah dihapus'
    query_id(request).delete()
    DBSession.flush()   
    
    return {'success':True, "msg":msg}
    