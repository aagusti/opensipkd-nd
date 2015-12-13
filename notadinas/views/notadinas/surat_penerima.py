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
    Surat, SuratDetail, PenerimaSurat, Disposisi, DisposisiComment, Job, Pegawai
    )
from ...models.pemda import (
    Unit, Urusan
    )
from datatables import ColumnDT, DataTables
from datetime import datetime,date
from ...tools import create_now, get_settings, Upload, file_type
from ...views.base_view import _DTstrftime,_number_format

SESS_ADD_FAILED = 'Tambah surat-penerima gagal'
SESS_EDIT_FAILED = 'Edit surat-penerima gagal'

##########                    
# Action #
##########    
@view_config(route_name='notadinas-surat-penerima-act', renderer='json',
             permission='notadinas-surat-penerima-act')
def view_act(request):
    ses = request.session
    req = request
    params   = req.params
    url_dict = req.matchdict

    if url_dict['act']=='grid':
        # defining columns
        surat_id = url_dict['surat_id'].isdigit() and url_dict['surat_id'] or 0
        columns = []
        columns.append(ColumnDT('id'))
        columns.append(ColumnDT('surat_id'))
        columns.append(ColumnDT('pegawai_id'))
        columns.append(ColumnDT('pegawais.kode'))
        columns.append(ColumnDT('pegawais.nama'))
        columns.append(ColumnDT('tanggal', filter=_DTstrftime))
        columns.append(ColumnDT('disabled'))
        
        query = DBSession.query(PenerimaSurat).\
                          join(Surat, Pegawai).\
                          filter(PenerimaSurat.surat_id   == surat_id,
                                 PenerimaSurat.pegawai_id == Pegawai.id,
                          )
                          
        rowTable = DataTables(req, PenerimaSurat, query, columns)
        return rowTable.output_result()
			
#######    
# Add #
#######
@view_config(route_name='notadinas-surat-penerima-add', renderer='json',
             permission='notadinas-surat-penerima-add')
def view_add(request):
    req = request
    ses = req.session
    params   = req.params
    url_dict = req.matchdict
    surat_id = 'surat_id' in url_dict and url_dict['surat_id'] or 0
    controls = dict(request.POST.items())
    
    surat_penerima_id = 'surat_penerima_id' in controls and controls['surat_penerima_id'] or 0
    pegawai_id        = 'pegawai_id'        in controls and controls['pegawai_id']        or 0
    #Cek dulu ada penyusup gak dengan mengecek sessionnya
    surat = DBSession.query(Surat)\
                     .filter(Surat.id==surat_id).first()
    if not surat:
        return {"success": False, 'msg':'Surat tidak ditemukan'}
    
    #Cek apakah penerima sudah terpakai apa belum
    penerima_surat = DBSession.query(PenerimaSurat)\
                              .filter(PenerimaSurat.surat_id == surat_id,
                                      PenerimaSurat.pegawai_id == pegawai_id).first()
    if penerima_surat:
        return {"success": False, 'msg':'Penerima tidak boleh sama.'}
    
    #Cek lagi ditakutkan ada yang iseng inject script
    if surat_penerima_id:
        row = DBSession.query(PenerimaSurat)\
                  .join(Surat)\
                  .filter(PenerimaSurat.id==surat_penerima_id,
                          PenerimaSurat.surat_id==surat_id).first()
        if not row:
            return {"success": False, 'msg':'Penerima tidak ditemukan'}
    else:
        row = PenerimaSurat()
            
    row.surat_id    = surat_id
    row.pegawai_id  = controls['pegawai_id']
    row.p_kode      = controls['p_kode']
    row.p_nama      = controls['p_nama']
    row.user_id     = req.user.id
    row.tanggal     = datetime.now()
    row.disabled    = 'disabled' in controls and 1 or 0
	
    DBSession.add(row)
    DBSession.flush()
	
    return {"success": True, 'id': row.id, "msg":'Success tambah Penerima Surat.'}


########
# Edit #
########
def route_list(request):
    return HTTPFound(location=request.route_url('notadinas-surat-edit',id=request.matchdict['surat_id']))
    
def query_id(request):
    return DBSession.query(PenerimaSurat).filter(PenerimaSurat.id==request.matchdict['id'],
                                                 PenerimaSurat.surat_id==request.matchdict['surat_id'])
    
def id_not_found(request):    
    msg = 'Surat ID %s not found.' % request.matchdict['id']
    request.session.flash(msg, 'error')
    return route_list(request)

##########
# Delete #
##########    
@view_config(route_name='notadinas-surat-penerima-delete', renderer='json',
             permission='notadinas-surat-penerima-delete')
def view_delete(request):
    q = query_id(request)
    row = q.first()
    
    if not row:
        return {'success':False, "msg":self.id_not_found()}

    msg = 'Data sudah dihapus'
    query_id(request).delete()
    DBSession.flush()   
    
    return {'success':True, "msg":msg}
    