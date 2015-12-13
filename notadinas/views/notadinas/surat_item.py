import os
import colander
from email.utils import parseaddr
from sqlalchemy import not_, func, cast, BigInteger, String
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
    DBSession,
    )
from ...models.notadinas import (
    Surat, SuratDetail, Disposisi, DisposisiComment, Job
    )
from ...models.pemda import (
    Unit, Urusan
    )
from datatables import ColumnDT, DataTables
from datetime import datetime,date
from ...tools import create_now, get_settings, Upload, file_type
from ...views.base_view import _DTstrftime,_number_format

SESS_ADD_FAILED = 'Tambah surat-item gagal'
SESS_EDIT_FAILED = 'Edit surat-item gagal'

tmpstore = FileUploadTempStore()

##########                    
# Action #
##########    
@view_config(route_name='notadinas-surat-item-act', renderer='json',
             permission='notadinas-surat-item-act')
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
        columns.append(ColumnDT('name'))
        columns.append(ColumnDT('size',filter=_number_format))
        
        query = DBSession.query(SuratDetail).\
                          join(Surat).\
                          filter(SuratDetail.surat_id==surat_id
                          )
                          
        rowTable = DataTables(req, SuratDetail, query, columns)
        return rowTable.output_result()
 			
class DbUpload(Upload):
    def __init__(self):
        settings = get_settings()
        dir_path = os.path.realpath(settings['static_files'])
        Upload.__init__(self, dir_path)
        
    def save(self, request, name, surat_id):
        fullpath = Upload.save(self, request, name)
        msg = 'File {fullpath} sudah disimpan.'
        msg = msg.format(fullpath=fullpath)
        request.session.flash(msg)
		
        row = SuratDetail()
        row.path     = fullpath[len(self.dir_path)+1:]
        row.name     = request.POST[name].filename
        row.size     = os.stat(fullpath).st_size
        row.mime     = file_type(fullpath)
        row.user_id  = request.user.id
        row.surat_id = surat_id
		
        DBSession.add(row)
        DBSession.flush()  
        return row

#######    
# Add #
#######
@view_config(route_name='notadinas-surat-item-add', renderer='json',
             permission='notadinas-surat-item-add')
def view_add(request):
    req = request
    ses = req.session
    params   = req.params
    url_dict = req.matchdict

    surat_id = 'surat_id' in url_dict and url_dict['surat_id'] or 0
    print '---------------surat id--------------------',surat_id
    controls = dict(request.POST.items())
    
    surat_item_id = 'surat_item_id' in controls and controls['surat_item_id'] or 0
    upload        = 'upload'        in controls and controls['upload']        or ''
    print '---------------surat item id---------------',surat_item_id
    print '---------------upload----------------------',upload
	
	#Cek dulu ada penyusup gak dengan mengecek sessionnya
    surat = DBSession.query(Surat)\
                     .filter(Surat.id==surat_id).first()
    if not surat:
        return {"success": False, 'msg':'Surat tidak ditemukan'}
    
    #Cek lagi ditakutkan ada yang iseng inject script
    if surat_item_id:
        row = DBSession.query(SuratDetail)\
                       .join(Surat)\
                       .filter(SuratDetail.id==surat_item_id,
                               SuratDetail.surat_id==surat_id).first()
        if not row:
            return {"success": False, 'msg':'File tidak ditemukan'}
    else:
        dbu = DbUpload()
    dbu.save(req, upload, surat_id)
	
    return {"success": True, 'id': row.id, "msg":'Success tambah file surat.'}


########
# Edit #
########
def route_list(request):
    return HTTPFound(location=request.route_url('notadinas-surat-edit',id=request.matchdict['surat_id']))
    
def query_id(request):
    return DBSession.query(SuratDetail).filter(SuratDetail.id==request.matchdict['id'],
                                               SuratDetail.surat_id==request.matchdict['surat_id'])
    
def id_not_found(request):    
    msg = 'Surat ID %s not found.' % request.matchdict['id']
    request.session.flash(msg, 'error')
    return route_list(request)

##########
# Delete #
##########    
@view_config(route_name='notadinas-surat-item-delete', renderer='json',
             permission='notadinas-surat-item-delete')
def view_delete(request):
    q = query_id(request)
    row = q.first()
    b   = row.path
    
    if not row:
        return {'success':False, "msg":self.id_not_found()}
    
    # Delete file in folder files env #
    settings = get_settings()
    dir_path = os.path.realpath(settings['static_files']) 
    print "--------------Tempat file---------------",dir_path  
    print "---------------Nama Path----------------",b      
    filename = os.path.join(dir_path, b)
    os.remove(filename) 
    
    # Delete database #
    msg = 'Data sudah dihapus'
    query_id(request).delete()
    DBSession.flush()   
    
    return {'success':True, "msg":msg}


############
# Download #
############    
@view_config(route_name='notadinas-surat-item-download', renderer='json',
             permission='notadinas-surat-item-download')
def view_download(request):
    q   = query_id(request)
    row = q.first()
    a   = row.id
    b   = row.path
    c   = row.name
    d   = row.mime
    
    if not row:
        return {'success':False, "msg":self.id_not_found()}

    msg = 'Data sudah didownload'
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