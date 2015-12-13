import os
import colander
from email.utils import parseaddr
from sqlalchemy import not_, func, cast, BigInteger, String
from sqlalchemy.orm import aliased
from pyramid.view import (
    view_config,
    )
from pyramid.response import (
    Response,
    FileIter,
    )
from pyramid.httpexceptions import (
    HTTPFound,
    )
from deform.interfaces import FileUploadTempStore
from deform import (
    Form,
    widget,
    ValidationFailure,
    FileData,
    )
from ...models import(
    DBSession, User
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

SESS_ADD_FAILED = 'Tambah surat-outbox-item gagal'
SESS_EDIT_FAILED = 'Edit surat-outbox-item gagal'

tmpstore = FileUploadTempStore()

##########                    
# Action #
##########    
@view_config(route_name='notadinas-surat-outbox-item-act', renderer='json',
             permission='notadinas-surat-outbox-item-act')
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
        columns.append(ColumnDT('na'))
        columns.append(ColumnDT('komentar'))
        
        user1db = aliased(User)
        
        surat_id = DBSession.query(Disposisi.surat_id).\
                          filter(Disposisi.id==disposisi_id,
                          )
        query = DBSession.query(DisposisiComment.id,
                                DisposisiComment.disposisi_id,
                                user1db.user_name.label('na'),
                                DisposisiComment.komentar).\
                          join(Disposisi).\
                          outerjoin(user1db, DisposisiComment.user_id == user1db.id).\
                          filter(DisposisiComment.disposisi_id==Disposisi.id,
                                 Disposisi.surat_id==surat_id,
                          )
                          
        rowTable = DataTables(req, DisposisiComment, query, columns)
        return rowTable.output_result()

    elif url_dict['act']=='file':
        disposisi_id = url_dict['disposisi_id'].isdigit() and url_dict['disposisi_id'] or 0
        columns = []
        columns.append(ColumnDT('id'))
        columns.append(ColumnDT('surat_id'))
        columns.append(ColumnDT('name'))
        columns.append(ColumnDT('size',filter=_number_format))
        
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
@view_config(route_name='notadinas-surat-outbox-item-add', renderer='json',
             permission='notadinas-surat-outbox-item-add')
def view_add(request):
    req = request
    ses = req.session
    params   = req.params
    url_dict = req.matchdict

    disposisi_id = 'disposisi_id' in url_dict and url_dict['disposisi_id'] or 0
    print '---------------disposisi id----------------',disposisi_id
    controls = dict(request.POST.items())
    
    disposisi_item_id = 'disposisi_item_id' in controls and controls['disposisi_item_id'] or 0
    print '---------------disposisi item id-----------',disposisi_item_id
    print '---------------komentar--------------------',controls['komentar']
	
	#Cek dulu ada penyusup gak dengan mengecek sessionnya
    disposisi = DBSession.query(Disposisi)\
                         .filter(Disposisi.id==disposisi_id).first()
    if not disposisi:
        return {"success": False, 'msg':'Surat masuk tidak ditemukan'}
    
    #Cek apakah komentar sudah terpakai apa belum
    komen = DBSession.query(DisposisiComment)\
                      .filter(DisposisiComment.disposisi_id == disposisi_id,
                              DisposisiComment.komentar     == controls['komentar']).first()
    if komen:
        return {"success": False, 'msg':'Komentar tidak boleh sama.'}
    
    #Cek lagi ditakutkan ada yang iseng inject script
    if disposisi_item_id:
        row = DBSession.query(DisposisiComment)\
                       .join(Disposisi)\
                       .filter(DisposisiComment.id==disposisi_item_id,
                               DisposisiComment.disposisi_id==disposisi_id).first()
        if not row:
            return {"success": False, 'msg':'Komentar tidak ditemukan'}
    else:
        row = DisposisiComment()
    row.disposisi_id = disposisi_id
    row.user_id      = request.user.id
    row.komentar     = controls['komentar']
	
    DBSession.add(row)
    DBSession.flush()
	
    return {"success": True, 'id': row.id, "msg":'Success tambah komentar.'}


########
# Edit #
########
def route_list(request):
    return HTTPFound(location=request.route_url('notadinas-surat-outbox-edit',id=request.matchdict['disposisi_id']))
    
def query_id(request):
    return DBSession.query(DisposisiComment).filter(DisposisiComment.id==request.matchdict['id'],
                                                    DisposisiComment.disposisi_id==request.matchdict['disposisi_id'])
    
def id_not_found(request):    
    msg = 'Surat keluar ID %s not found.' % request.matchdict['id']
    request.session.flash(msg, 'error')
    return route_list(request)

##########
# Delete #
##########    
@view_config(route_name='notadinas-surat-outbox-item-delete', renderer='json',
             permission='notadinas-surat-outbox-item-delete')
def view_delete(request):
    q = query_id(request)
    row = q.first()
    print'----------row-----------',row
    
    if not row:
        request.session.flash('Maaf datanya tidak bisa dihapus.', 'error')
        return route_list(request)
        
    a = row.user_id
    b = request.user.id
    if a != b:
        request.session.flash('Maaf datanya tidak bisa dihapus.', 'error')
        return route_list(request)
        

    msg = 'Data sudah dihapus'
    query_id(request).delete()
    DBSession.flush()   
    
    return {'success':True, "msg":msg}

############
# Download #
############    
@view_config(route_name='notadinas-surat-outbox-item-download', renderer='json',
             permission='notadinas-surat-outbox-item-download')
def view_download(request):
    req = request
    url_dict = req.matchdict
    id1 = url_dict['id'].isdigit() and url_dict['id'] or 0
    dis = url_dict['disposisi_id'].isdigit() and url_dict['disposisi_id'] or 0
    
    si = DBSession.query(Disposisi.surat_id).\
                      filter(Disposisi.id==dis,
                      )
    row = DBSession.query(SuratDetail
                  ).filter(SuratDetail.id==id1
                  ).first()
    b   = row.path
    c   = row.name
    d   = row.mime
    
    if not row:
        return {'success':False, "msg":self.id_not_found()}

    settings = get_settings()
    dir_path = os.path.realpath(settings['static_files'])
        
    filename = os.path.join(dir_path, b)
    headers  = [('Content-Disposition', 'attachment; filename=' + str(c))]
    response = Response(content_type=d, headerlist=headers)
    f = open(filename)
    response.app_iter = FileIter(f)
    print "----------------path------------------",b
    print "--------------nama file---------------",c
    print "------------content type--------------",d
    return response   