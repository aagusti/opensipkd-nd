import os
import unittest
import os.path
import uuid
import urlparse

from datetime import datetime
from sqlalchemy import *
from sqlalchemy.orm import aliased
from sqlalchemy.sql.expression import literal_column
from pyramid.view import (view_config,)
from pyramid.httpexceptions import ( HTTPFound, )
import colander
from deform import (Form, widget, ValidationFailure, )
    
from datatables import ColumnDT, DataTables

from pyjasper import (JasperGenerator)
from pyjasper import (JasperGeneratorWithSubreport)
import xml.etree.ElementTree as ET
from pyramid.path import AssetResolver

from ...models import DBSession, User
from ...models.notadinas import *
from ...models.pemda import *
from ...views.base_view import _DTstrftime
from datetime import datetime

def get_rpath(filename):
    a = AssetResolver('notadinas')
    resolver = a.resolve(''.join(['reports/',filename]))
    return resolver.abspath()
    
angka = {1:'satu',2:'dua',3:'tiga',4:'empat',5:'lima',6:'enam',7:'tujuh',\
         8:'delapan',9:'sembilan'}
b = ' puluh '
c = ' ratus '
d = ' ribu '
e = ' juta '
f = ' milyar '
g = ' triliun '
def Terbilang(x):   
    y = str(x)         
    n = len(y)        
    if n <= 3 :        
        if n == 1 :   
            if y == '0' :   
                return ''   
            else :         
                return angka[int(y)]   
        elif n == 2 :
            if y[0] == '1' :                
                if y[1] == '1' :
                    return 'sebelas'
                elif y[0] == '0':
                    x = y[1]
                    return Terbilang(x)
                elif y[1] == '0' :
                    return 'sepuluh'
                else :
                    return angka[int(y[1])] + ' belas'
            elif y[0] == '0' :
                x = y[1]
                return Terbilang(x)
            else :
                x = y[1]
                return angka[int(y[0])] + b + Terbilang(x)
        else :
            if y[0] == '1' :
                x = y[1:]
                return 'seratus ' + Terbilang(x)
            elif y[0] == '0' : 
                x = y[1:]
                return Terbilang(x)
            else :
                x = y[1:]
                return angka[int(y[0])] + c + Terbilang(x)
    elif 3< n <=6 :
        p = y[-3:]
        q = y[:-3]
        if q == '1' :
            return 'seribu' + Terbilang(p)
        elif q == '000' :
            return Terbilang(p)
        else:
            return Terbilang(q) + d + Terbilang(p)
    elif 6 < n <= 9 :
        r = y[-6:]
        s = y[:-6]
        return Terbilang(s) + e + Terbilang(r)
    elif 9 < n <= 12 :
        t = y[-9:]
        u = y[:-9]
        return Terbilang(u) + f + Terbilang(t)
    else:
        v = y[-12:]
        w = y[:-12]
        return Terbilang(w) + g + Terbilang(v)

class ViewNotadinasLap():
    def __init__(self, context, request):
        self.context = context
        self.request = request
		
    # LAPORAN Surat
    @view_config(route_name="notadinas-surat-report", renderer="templates/report_notadinas/surat_report.pt", permission="notadinas-surat-report")
    def surat(self):
        params = self.request.params
        return dict()

    @view_config(route_name="notadinas-surat-report-act", renderer="json", permission="notadinas-surat-report-act")
    def surat_act(self):
        global mulai, selesai, unit
        req      = self.request
        params   = req.params
        url_dict = req.matchdict
 
        unit         = 'unit'         in params and params['unit']         or 0
        jenis        = 'jenis'        in params and params['jenis']        or 0
        mulai        = 'mulai'        in params and params['mulai']        or 0
        selesai      = 'selesai'      in params and params['selesai']      or 0
        surat_id     = 'surat_id'     in params and params['surat_id']     or 0
        disposisi_id = 'disposisi_id' in params and params['disposisi_id'] or 0
        
		# Khusus untuk modul master #
        pegawai_id   = 'pegawai_id'   in params and params['pegawai_id']   or 0
        jabatan_id   = 'jabatan_id'   in params and params['jabatan_id']   or 0
        job_id       = 'job_id'       in params and params['job_id']       or 0
        urusan_id    = 'urusan_id'    in params and params['urusan_id']    or 0
        uniker_id    = 'uniker_id'    in params and params['uniker_id']    or 0
		
        if url_dict['act']=='laporan' :
            # Jenis laporan surat #
            if jenis == '1' :
                u = req.user.id
                if u == 1:
                    query = DBSession.query(Surat.kode.label('surat_kd'),
                                            Surat.from_to.label('surat_ft'),
                                            Surat.nama.label('surat_nm'),
                                            Surat.no_surat.label('surat_ns'),
                                            Surat.tanggal_surat.label('surat_ts'),
                                            Surat.tanggal_terima.label('surat_tt'),
                                            case([(Surat.sifat==0,"Biasa"),
                                                  (Surat.sifat==1,"Segera"),
                                                  (Surat.sifat==2,"Sangat Segera"),
                                                  (Surat.sifat==3,"Rahasia")], else_="").label('surat_sf'),
                                            Surat.agenda.label('surat_a'),
                                            case([(Surat.status==0,"Masuk"),
                                                  (Surat.status==1,"Keluar"),
                                                  (Surat.status==2,"Diteruskan")], else_="").label('surat_s'),
                                            Surat.indeks.label('surat_i'),
                                            Surat.lampiran.label('surat_l'),
                                    ).filter(Surat.tanggal_terima.between(mulai,selesai)
                                    ).order_by(Surat.from_to, 	 					 	 										 
                                    ).all()
                    generator = surat_laporan_Generator()
                    pdf = generator.generate(query)
                    response=req.response
                    response.content_type="application/pdf"
                    response.content_disposition='filename=output.pdf' 
                    response.write(pdf)
                    return response
                else:
                    query = DBSession.query(Surat.kode.label('surat_kd'),
                                            Surat.from_to.label('surat_ft'),
                                            Surat.nama.label('surat_nm'),
                                            Surat.no_surat.label('surat_ns'),
                                            Surat.tanggal_surat.label('surat_ts'),
                                            Surat.tanggal_terima.label('surat_tt'),
                                            case([(Surat.sifat==0,"Biasa"),
                                                  (Surat.sifat==1,"Segera"),
                                                  (Surat.sifat==2,"Sangat Segera"),
                                                  (Surat.sifat==3,"Rahasia")], else_="").label('surat_sf'),
                                            Surat.agenda.label('surat_a'),
                                            case([(Surat.status==0,"Masuk"),
                                                  (Surat.status==1,"Keluar"),
                                                  (Surat.status==2,"Diteruskan")], else_="").label('surat_s'),
                                            Surat.indeks.label('surat_i'),
                                            Surat.lampiran.label('surat_l'),
                                    ).filter(Surat.create_uid == u,
                                             Surat.tanggal_terima.between(mulai,selesai)
                                    ).order_by(Surat.from_to, 	 					 	 										 
                                    ).all()
                    generator = surat_laporan_Generator()
                    pdf = generator.generate(query)
                    response=req.response
                    response.content_type="application/pdf"
                    response.content_disposition='filename=output.pdf' 
                    response.write(pdf)
                    return response
                    
            # Jenis laporan Disposisi Masuk #        
            elif jenis == '2' :
                u = req.user.id
                if u == 1:
                    query = DBSession.query(Surat.from_to.label('surat_ft'),
                                            Surat.nama.label('surat_nm'),
                                            Surat.no_surat.label('surat_ns'),
                                            Disposisi.tanggal.label('dis_t'),
                                            Disposisi.notes.label('dis_n'),
                                            case([(Disposisi.need_feedback==0,"Tidak"),
                                                  (Disposisi.need_feedback==1,"Ya")], else_="").label('dis_nf'),
                                            Disposisi.date_feedback.label('dis_df'),
                                            case([(Disposisi.status==0,"Unread"),
                                                  (Disposisi.status==1,"Read"),
                                                  (Disposisi.status==2,"Diteruskan")], else_="").label('dis_s'),
                                            Disposisi.job_id.label('dis_j'),
                                    ).filter(Disposisi.surat_id == Surat.id,
                                             Disposisi.status   != 2                          
                                    ).order_by(Surat.from_to, 	 					 	 										 
                                    ).all()
                    generator = surat2_laporan_Generator()
                    pdf = generator.generate(query)
                    response=req.response
                    response.content_type="application/pdf"
                    response.content_disposition='filename=output.pdf' 
                    response.write(pdf)
                    return response
                else:
                    query = DBSession.query(Surat.from_to.label('surat_ft'),
                                            Surat.nama.label('surat_nm'),
                                            Surat.no_surat.label('surat_ns'),
                                            Disposisi.tanggal.label('dis_t'),
                                            Disposisi.notes.label('dis_n'),
                                            case([(Disposisi.need_feedback==0,"Tidak"),
                                                  (Disposisi.need_feedback==1,"Ya")], else_="").label('dis_nf'),
                                            Disposisi.date_feedback.label('dis_df'),
                                            case([(Disposisi.status==0,"Unread"),
                                                  (Disposisi.status==1,"Read"),
                                                  (Disposisi.status==2,"Diteruskan")], else_="").label('dis_s'),
                                            Disposisi.job_id.label('dis_j'),
                                    ).filter(Disposisi.surat_id == Surat.id,
                                             Disposisi.to_uid   == u                          
                                    ).order_by(Surat.from_to, 	 					 	 										 
                                    ).all()
                    generator = surat2_laporan_Generator()
                    pdf = generator.generate(query)
                    response=req.response
                    response.content_type="application/pdf"
                    response.content_disposition='filename=output.pdf' 
                    response.write(pdf)
                    return response
                    
            # Jenis laporan Disposisi Keluar #        
            else:
                u = req.user.id
                if u == 1:
                    query = DBSession.query(Surat.from_to.label('surat_ft'),
                                            Surat.nama.label('surat_nm'),
                                            Surat.no_surat.label('surat_ns'),
                                            Disposisi.tanggal.label('dis_t'),
                                            Disposisi.notes.label('dis_n'),
                                            case([(Disposisi.need_feedback==0,"Tidak"),
                                                  (Disposisi.need_feedback==1,"Ya")], else_="").label('dis_nf'),
                                            Disposisi.date_feedback.label('dis_df'),
                                            case([(Disposisi.status==0,"Unread"),
                                                  (Disposisi.status==1,"Read"),
                                                  (Disposisi.status==2,"Diteruskan")], else_="").label('dis_s'),
                                            Disposisi.job_id.label('dis_j'),
                                    ).filter(Disposisi.surat_id == Surat.id,
                                             Disposisi.status   == 2                          
                                    ).order_by(Surat.from_to, 	 					 	 										 
                                    ).all()
                    generator = surat3_laporan_Generator()
                    pdf = generator.generate(query)
                    response=req.response
                    response.content_type="application/pdf"
                    response.content_disposition='filename=output.pdf' 
                    response.write(pdf)
                    return response
                else:
                    query = DBSession.query(Surat.from_to.label('surat_ft'),
                                            Surat.nama.label('surat_nm'),
                                            Surat.no_surat.label('surat_ns'),
                                            Disposisi.tanggal.label('dis_t'),
                                            Disposisi.notes.label('dis_n'),
                                            case([(Disposisi.need_feedback==0,"Tidak"),
                                                  (Disposisi.need_feedback==1,"Ya")], else_="").label('dis_nf'),
                                            Disposisi.date_feedback.label('dis_df'),
                                            case([(Disposisi.status==0,"Unread"),
                                                  (Disposisi.status==1,"Read"),
                                                  (Disposisi.status==2,"Diteruskan")], else_="").label('dis_s'),
                                            Disposisi.job_id.label('dis_j'),
                                    ).filter(Disposisi.surat_id == Surat.id,
                                             Disposisi.from_uid == u                          
                                    ).order_by(Surat.from_to, 	 					 	 										 
                                    ).all()
                    generator = surat3_laporan_Generator()
                    pdf = generator.generate(query)
                    response=req.response
                    response.content_type="application/pdf"
                    response.content_disposition='filename=output.pdf' 
                    response.write(pdf)
                    return response
            
        elif url_dict['act']=='surat' :
            query = DBSession.query(Surat.kode.label('surat_kd'),
                                    Surat.from_to.label('surat_ft'),
                                    Surat.nama.label('surat_nm'),
                                    Surat.no_surat.label('surat_ns'),
                                    Surat.tanggal_surat.label('surat_ts'),
                                    Surat.tanggal_terima.label('surat_tt'),
                                    case([(Surat.sifat==0,"Biasa"),
                                          (Surat.sifat==1,"Segera"),
                                          (Surat.sifat==2,"Sangat Segera"),
                                          (Surat.sifat==3,"Rahasia")], else_="").label('surat_sf'),
                                    Surat.agenda.label('surat_a'),
                                    case([(Surat.status==0,"Masuk"),
                                          (Surat.status==1,"Keluar"),
                                          (Surat.status==2,"Diteruskan")], else_="").label('surat_s'),
                                    Surat.indeks.label('surat_i'),
                                    Surat.lampiran.label('surat_l'),
                            ).filter(Surat.id == surat_id,
                            ).order_by(Surat.from_to, 	 					 	 										 
                            ).all()
            generator = surat_Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
            
        elif url_dict['act']=='surat2' :
            u = req.user.id
            if u == 1:
                query = DBSession.query(Surat.kode.label('surat_kd'),
                                        Surat.from_to.label('surat_ft'),
                                        Surat.nama.label('surat_nm'),
                                        Surat.no_surat.label('surat_ns'),
                                        Surat.tanggal_surat.label('surat_ts'),
                                        Surat.tanggal_terima.label('surat_tt'),
                                        case([(Surat.sifat==0,"Biasa"),
                                              (Surat.sifat==1,"Segera"),
                                              (Surat.sifat==2,"Sangat Segera"),
                                              (Surat.sifat==3,"Rahasia")], else_="").label('surat_sf'),
                                        Surat.agenda.label('surat_a'),
                                        case([(Surat.status==0,"Masuk"),
                                              (Surat.status==1,"Keluar"),
                                              (Surat.status==2,"Diteruskan")], else_="").label('surat_s'),
                                        Surat.indeks.label('surat_i'),
                                        Surat.lampiran.label('surat_l'),
                                ).order_by(Surat.from_to, 	 					 	 										 
                                ).all()
                generator = surat2_Generator()
                pdf = generator.generate(query)
                response=req.response
                response.content_type="application/pdf"
                response.content_disposition='filename=output.pdf' 
                response.write(pdf)
                return response
            else:
                query = DBSession.query(Surat.kode.label('surat_kd'),
                                        Surat.from_to.label('surat_ft'),
                                        Surat.nama.label('surat_nm'),
                                        Surat.no_surat.label('surat_ns'),
                                        Surat.tanggal_surat.label('surat_ts'),
                                        Surat.tanggal_terima.label('surat_tt'),
                                        case([(Surat.sifat==0,"Biasa"),
                                              (Surat.sifat==1,"Segera"),
                                              (Surat.sifat==2,"Sangat Segera"),
                                              (Surat.sifat==3,"Rahasia")], else_="").label('surat_sf'),
                                        Surat.agenda.label('surat_a'),
                                        case([(Surat.status==0,"Masuk"),
                                              (Surat.status==1,"Keluar"),
                                              (Surat.status==2,"Diteruskan")], else_="").label('surat_s'),
                                        Surat.indeks.label('surat_i'),
                                        Surat.lampiran.label('surat_l'),
                                ).filter(Surat.create_uid == u                          
                                ).order_by(Surat.from_to, 	 					 	 										 
                                ).all()
                generator = surat2_Generator()
                pdf = generator.generate(query)
                response=req.response
                response.content_type="application/pdf"
                response.content_disposition='filename=output.pdf' 
                response.write(pdf)
                return response
            
        elif url_dict['act']=='tracking_surat' :
            subq1 = DBSession.query(Disposisi.id,
                                    Disposisi.surat_id,
                                    Disposisi.dis_id,
                                    Pegawai.nama.label('p1_nm'),
                                    Jabatan.nama.label('j1_nm')
                            ).filter(Pegawai.user_id==Disposisi.to_uid,
                                     Jabatan.id==Pegawai.jabatan_id
                            ).subquery()
                            
            subq2 = DBSession.query(Disposisi.id,
                                    Disposisi.surat_id,
                                    Disposisi.dis_id,
                                    Pegawai.nama.label('p2_nm'),
                                    Jabatan.nama.label('j2_nm')
                            ).filter(Pegawai.user_id==Disposisi.to_uid,
                                     Jabatan.id==Pegawai.jabatan_id
                            ).subquery()
                            
            subq3 = DBSession.query(Disposisi.id,
                                    Disposisi.surat_id,
                                    Disposisi.dis_id,
                                    Pegawai.nama.label('p3_nm'),
                                    Jabatan.nama.label('j3_nm')
                            ).filter(Pegawai.user_id==Disposisi.to_uid,
                                     Jabatan.id==Pegawai.jabatan_id
                            ).subquery()
                            
            subq4 = DBSession.query(Disposisi.id,
                                    Disposisi.surat_id,
                                    Disposisi.dis_id,
                                    Pegawai.nama.label('p4_nm'),
                                    Jabatan.nama.label('j4_nm')
                            ).filter(Pegawai.user_id==Disposisi.to_uid,
                                     Jabatan.id==Pegawai.jabatan_id
                            ).subquery()
                            
            jab1 = aliased(Jabatan)
            peg1 = aliased(Pegawai)
            
            query = DBSession.query(Surat.id.label('sid'),
                                    Surat.create_uid.label('uid'),
                                    Surat.from_to.label('surat_ft'),
                                    Surat.nama.label('surat_nm'),
                                    Surat.no_surat.label('surat_ns'),
                                    Surat.tanggal_surat.label('surat_ts'),
                                    Surat.tanggal_terima.label('surat_tt'),
                                    Disposisi.id.label('did'),
                                    Pegawai.kode.label('p_kd'),
                                    Pegawai.nama.label('p_nm'),
                                    Jabatan.nama.label('j_nm'),
                                    peg1.nama.label('p1_nm'),
                                    jab1.nama.label('j1_nm'),
                                    subq1.c.p1_nm.label('p2_nm'),
                                    subq1.c.j1_nm.label('j2_nm'),
                                    subq2.c.p2_nm.label('p3_nm'),
                                    subq2.c.j2_nm.label('j3_nm'),
                                    subq3.c.p3_nm.label('p4_nm'),
                                    subq3.c.j3_nm.label('j4_nm'),
                                    subq4.c.p4_nm.label('p5_nm'),
                                    subq4.c.j4_nm.label('j5_nm'),
                            ).join(Disposisi
                            ).outerjoin(subq1, and_(subq1.c.surat_id==Surat.id, subq1.c.dis_id==Disposisi.id)
                            ).outerjoin(subq2, and_(subq2.c.surat_id==Surat.id, subq2.c.dis_id==subq1.c.id)   
                            ).outerjoin(subq3, and_(subq3.c.surat_id==Surat.id, subq3.c.dis_id==subq2.c.id)
                            ).outerjoin(subq4, and_(subq4.c.surat_id==Surat.id, subq4.c.dis_id==subq3.c.id)      
                            ).filter(Disposisi.surat_id == surat_id,
                                     Disposisi.surat_id == Surat.id, 
                                     Disposisi.dis_id == 0,
                                     Pegawai.user_id == Disposisi.from_uid,
                                     Pegawai.jabatan_id == Jabatan.id,
                                     peg1.user_id == Disposisi.to_uid,
                                     peg1.jabatan_id == jab1.id,
                            #).order_by(Surat.no_surat, 	 					 	 										 
                            ).all()
            generator = tracking_surat_Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
		
        elif url_dict['act']=='surat_masuk' :
            query = DBSession.query(Surat.from_to.label('surat_ft'),
                                    Surat.nama.label('surat_nm'),
                                    Surat.no_surat.label('surat_ns'),
                                    Disposisi.tanggal.label('dis_t'),
                                    Disposisi.notes.label('dis_n'),
                                    case([(Disposisi.need_feedback==0,"Tidak"),
                                          (Disposisi.need_feedback==1,"Ya")], else_="").label('dis_nf'),
                                    Disposisi.date_feedback.label('dis_df'),
                                    case([(Disposisi.status==0,"Unread"),
                                          (Disposisi.status==1,"Read"),
                                          (Disposisi.status==2,"Diteruskan")], else_="").label('dis_s'),
                                    Disposisi.job_id.label('dis_j'),
                            ).filter(Disposisi.id       == disposisi_id,
                                     Disposisi.surat_id == Surat.id,                        
                            ).order_by(Surat.from_to, 	 					 	 										 
                            ).all()
            generator = surat_masuk_Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
		
        elif url_dict['act']=='surat_masuk_all' :
            u = req.user.id
            if u == 1:
                query = DBSession.query(Surat.from_to.label('surat_ft'),
                                        Surat.nama.label('surat_nm'),
                                        Surat.no_surat.label('surat_ns'),
                                        Disposisi.tanggal.label('dis_t'),
                                        Disposisi.notes.label('dis_n'),
                                        case([(Disposisi.need_feedback==0,"Tidak"),
                                              (Disposisi.need_feedback==1,"Ya")], else_="").label('dis_nf'),
                                        Disposisi.date_feedback.label('dis_df'),
                                        case([(Disposisi.status==0,"Unread"),
                                              (Disposisi.status==1,"Read"),
                                              (Disposisi.status==2,"Diteruskan")], else_="").label('dis_s'),
                                        Disposisi.job_id.label('dis_j'),
                                ).filter(Disposisi.surat_id == Surat.id,
                                         Disposisi.status   != 2                          
                                ).order_by(Surat.from_to, 	 					 	 										 
                                ).all()
                generator = surat_masuk_all_Generator()
                pdf = generator.generate(query)
                response=req.response
                response.content_type="application/pdf"
                response.content_disposition='filename=output.pdf' 
                response.write(pdf)
                return response
            else:
                query = DBSession.query(Surat.from_to.label('surat_ft'),
                                        Surat.nama.label('surat_nm'),
                                        Surat.no_surat.label('surat_ns'),
                                        Disposisi.tanggal.label('dis_t'),
                                        Disposisi.notes.label('dis_n'),
                                        case([(Disposisi.need_feedback==0,"Tidak"),
                                              (Disposisi.need_feedback==1,"Ya")], else_="").label('dis_nf'),
                                        Disposisi.date_feedback.label('dis_df'),
                                        case([(Disposisi.status==0,"Unread"),
                                              (Disposisi.status==1,"Read"),
                                              (Disposisi.status==2,"Diteruskan")], else_="").label('dis_s'),
                                        Disposisi.job_id.label('dis_j'),
                                ).filter(Disposisi.surat_id == Surat.id,
                                         Disposisi.to_uid   == u                          
                                ).order_by(Surat.from_to, 	 					 	 										 
                                ).all()
                generator = surat_masuk_all_Generator()
                pdf = generator.generate(query)
                response=req.response
                response.content_type="application/pdf"
                response.content_disposition='filename=output.pdf' 
                response.write(pdf)
                return response
		
        elif url_dict['act']=='surat_keluar' :
            query = DBSession.query(Surat.from_to.label('surat_ft'),
                                    Surat.nama.label('surat_nm'),
                                    Surat.no_surat.label('surat_ns'),
                                    Disposisi.tanggal.label('dis_t'),
                                    Disposisi.notes.label('dis_n'),
                                    case([(Disposisi.need_feedback==0,"Tidak"),
                                          (Disposisi.need_feedback==1,"Ya")], else_="").label('dis_nf'),
                                    Disposisi.date_feedback.label('dis_df'),
                                    case([(Disposisi.status==0,"Unread"),
                                          (Disposisi.status==1,"Read"),
                                          (Disposisi.status==2,"Diteruskan")], else_="").label('dis_s'),
                                    Disposisi.job_id.label('dis_j'),
                            ).filter(Disposisi.id       == disposisi_id,
                                     Disposisi.surat_id == Surat.id,                       
                            ).order_by(Surat.from_to, 	 					 	 										 
                            ).all()
            generator = surat_keluar_Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
		
        elif url_dict['act']=='surat_keluar_all' :
            u = req.user.id
            if u == 1:
                query = DBSession.query(Surat.from_to.label('surat_ft'),
                                        Surat.nama.label('surat_nm'),
                                        Surat.no_surat.label('surat_ns'),
                                        Disposisi.tanggal.label('dis_t'),
                                        Disposisi.notes.label('dis_n'),
                                        case([(Disposisi.need_feedback==0,"Tidak"),
                                              (Disposisi.need_feedback==1,"Ya")], else_="").label('dis_nf'),
                                        Disposisi.date_feedback.label('dis_df'),
                                        case([(Disposisi.status==0,"Unread"),
                                              (Disposisi.status==1,"Read"),
                                              (Disposisi.status==2,"Diteruskan")], else_="").label('dis_s'),
                                        Disposisi.job_id.label('dis_j'),
                                ).filter(Disposisi.surat_id == Surat.id,
                                         Disposisi.status   == 2                          
                                ).order_by(Surat.from_to, 	 					 	 										 
                                ).all()
                generator = surat_keluar_all_Generator()
                pdf = generator.generate(query)
                response=req.response
                response.content_type="application/pdf"
                response.content_disposition='filename=output.pdf' 
                response.write(pdf)
                return response
            else:
                query = DBSession.query(Surat.from_to.label('surat_ft'),
                                        Surat.nama.label('surat_nm'),
                                        Surat.no_surat.label('surat_ns'),
                                        Disposisi.tanggal.label('dis_t'),
                                        Disposisi.notes.label('dis_n'),
                                        case([(Disposisi.need_feedback==0,"Tidak"),
                                              (Disposisi.need_feedback==1,"Ya")], else_="").label('dis_nf'),
                                        Disposisi.date_feedback.label('dis_df'),
                                        case([(Disposisi.status==0,"Unread"),
                                              (Disposisi.status==1,"Read"),
                                              (Disposisi.status==2,"Diteruskan")], else_="").label('dis_s'),
                                        Disposisi.job_id.label('dis_j'),
                                ).filter(Disposisi.surat_id == Surat.id,
                                         Disposisi.from_uid == u                          
                                ).order_by(Surat.from_to, 	 					 	 										 
                                ).all()
                generator = surat_keluar_all_Generator()
                pdf = generator.generate(query)
                response=req.response
                response.content_type="application/pdf"
                response.content_disposition='filename=output.pdf' 
                response.write(pdf)
                return response
            
            
        ###############################		
		## Khusus untuk modul master ##
        ###############################	
		
        elif url_dict['act']=='pegawai' :
            query = DBSession.query(Pegawai.kode.label('pegawai_kd'),
                                    Pegawai.nama.label('pegawai_nm'),
                                    Unit.nama.label('unit_nm'),
                                    Jabatan.nama.label('jabatan_nm'),
                                    Pegawai.email,
                                    Pegawai.handphone,
                                    Pegawai.alamat,
                                    Pegawai.user_id.label('id1'),
                            ).join(Unit,Jabatan
                            ).filter(Pegawai.id         == pegawai_id, 	  
                                     Pegawai.unit_id    == Unit.id,	 	  
                                     Pegawai.jabatan_id == Jabatan.id,	 		 										 
                            ).all()
            generator = master_pegawai_Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response		
		
        elif url_dict['act']=='pegawai2' :
            query = DBSession.query(Pegawai.kode.label('pegawai_kd'),
                                    Pegawai.nama.label('pegawai_nm'),
                                    Unit.nama.label('unit_nm'),
                                    Jabatan.nama.label('jabatan_nm'),
                                    Pegawai.email,
                                    Pegawai.handphone,
                                    Pegawai.alamat,
                                    Pegawai.user_id.label('id1'),
                            ).join(Unit,Jabatan
                            ).filter(Pegawai.unit_id    == Unit.id,	 	  
                                     Pegawai.jabatan_id == Jabatan.id,	
                            ).order_by(Pegawai.nama, 				 		 										 
                            ).all()
            generator = master_pegawai2_Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response		
		
        elif url_dict['act']=='jabatan' :
            query = DBSession.query(Jabatan.kode.label('jabatan_kd'),
                                    Jabatan.nama.label('jabatan_nm'),
                                    Jabatan.parent_id.label('id1'),
                            ).filter(Jabatan.id == jabatan_id,  	 										 
                            ).all()
            generator = master_jabatan_Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response	
		
        elif url_dict['act']=='jabatan2' :
            query = DBSession.query(Jabatan.kode.label('jabatan_kd'),
                                    Jabatan.nama.label('jabatan_nm'),
                                    Jabatan.parent_id.label('id1'),		
                            ).order_by(Jabatan.kode, 	 				 										 
                            ).all()
            generator = master_jabatan2_Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
			
        elif url_dict['act']=='job' :
            query = DBSession.query(Job.kode.label('job_kd'),
                                    Job.nama.label('job_nm'),
                            ).filter(Job.id == job_id, 						
                            ).all()
            generator = master_job_Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response		
			
        elif url_dict['act']=='job2' :
            query = DBSession.query(Job.kode.label('job_kd'),
                                    Job.nama.label('job_nm'),
                            ).order_by(Job.kode, 						
                            ).all()
            generator = master_job2_Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response	
			
        elif url_dict['act']=='urusan' :
            query = DBSession.query(Urusan.kode.label('urusan_kd'),
                                    Urusan.nama.label('urusan_nm'),
                            ).filter(Urusan.id == urusan_id, 						
                            ).all()
            generator = master_urusan_Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
			
        elif url_dict['act']=='urusan2' :
            query = DBSession.query(Urusan.kode.label('urusan_kd'),
                                    Urusan.nama.label('urusan_nm'),
                            ).order_by(Urusan.kode, 						
                            ).all()
            generator = master_urusan2_Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response	
		
        elif url_dict['act']=='uniker' :
            query = DBSession.query(Unit.kode.label('unit_kd'),
                                    Unit.nama.label('unit_nm'),
                                    Urusan.kode.label('urusan_kd'),
                                    Urusan.nama.label('urusan_nm'),
                                    Unit.level_id,
                                    Unit.parent_id.label('id1'),
                            ).join(Urusan,
                            ).filter(Unit.id        == uniker_id, 	  
                                     Unit.urusan_id == Urusan.id,	 	 										 
                            ).all()
            generator = master_unit_Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response	
		
        elif url_dict['act']=='uniker2' :
            query = DBSession.query(Unit.kode.label('unit_kd'),
                                    Unit.nama.label('unit_nm'),
                                    Urusan.kode.label('urusan_kd'),
                                    Urusan.nama.label('urusan_nm'),
                                    Unit.level_id,
                                    Unit.parent_id.label('id1'),
                            ).join(Urusan,
                            ).filter(Unit.urusan_id == Urusan.id,	
                            ).order_by(Unit.kode, 	 					 	 										 
                            ).all()
            generator = master_unit2_Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
	
			
######################################################################			
#########################  JASPER GENERATOR  #########################
######################################################################	
		
# Surat #
class surat_Generator(JasperGenerator):
    def __init__(self):
        super(surat_Generator, self).__init__()
        self.reportname = get_rpath('Surat.jrxml')
        self.xpath = '/surat/surat'
        self.root = ET.Element('surat') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'surat')
            ET.SubElement(xml_greeting, "surat_kd").text  = row.surat_kd
            ET.SubElement(xml_greeting, "surat_ft").text  = row.surat_ft
            ET.SubElement(xml_greeting, "surat_nm").text  = row.surat_nm
            ET.SubElement(xml_greeting, "surat_ns").text  = row.surat_ns
            ET.SubElement(xml_greeting, "surat_ts").text  = unicode(row.surat_ts)
            ET.SubElement(xml_greeting, "surat_tt").text  = unicode(row.surat_tt)
            ET.SubElement(xml_greeting, "surat_sf").text  = row.surat_sf
            ET.SubElement(xml_greeting, "surat_a").text   = row.surat_a
            ET.SubElement(xml_greeting, "surat_s").text   = row.surat_s
            ET.SubElement(xml_greeting, "surat_i").text   = row.surat_i
            ET.SubElement(xml_greeting, "surat_l").text   = row.surat_l
        return self.root
        
# Surat (all) #
class surat2_Generator(JasperGenerator):
    def __init__(self):
        super(surat2_Generator, self).__init__()
        self.reportname = get_rpath('Surat_all.jrxml')
        self.xpath = '/surat/surat_all'
        self.root = ET.Element('surat') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'surat_all')
            ET.SubElement(xml_greeting, "surat_kd").text  = row.surat_kd
            ET.SubElement(xml_greeting, "surat_ft").text  = row.surat_ft
            ET.SubElement(xml_greeting, "surat_nm").text  = row.surat_nm
            ET.SubElement(xml_greeting, "surat_ns").text  = row.surat_ns
            ET.SubElement(xml_greeting, "surat_ts").text  = unicode(row.surat_ts)
            ET.SubElement(xml_greeting, "surat_tt").text  = unicode(row.surat_tt)
            ET.SubElement(xml_greeting, "surat_sf").text  = row.surat_sf
            ET.SubElement(xml_greeting, "surat_a").text   = row.surat_a
            ET.SubElement(xml_greeting, "surat_s").text   = row.surat_s
            ET.SubElement(xml_greeting, "surat_i").text   = row.surat_i
            ET.SubElement(xml_greeting, "surat_l").text   = row.surat_l
        return self.root		
        
# Tracking Surat #
class tracking_surat_Generator(JasperGenerator):
    def __init__(self):
        super(tracking_surat_Generator, self).__init__()
        self.reportname = get_rpath('Tracking_surat2.jrxml')
        self.xpath = '/surat/tracking_surat'
        self.root = ET.Element('surat') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'tracking_surat')
            ET.SubElement(xml_greeting, "surat_ft").text  = row.surat_ft
            ET.SubElement(xml_greeting, "surat_nm").text  = row.surat_nm
            ET.SubElement(xml_greeting, "surat_ns").text  = row.surat_ns
            ET.SubElement(xml_greeting, "surat_ts").text  = unicode(row.surat_ts)
            ET.SubElement(xml_greeting, "surat_tt").text  = unicode(row.surat_tt)
            ET.SubElement(xml_greeting, "uid").text       = unicode(row.uid)
            ET.SubElement(xml_greeting, "sid").text       = unicode(row.sid)
            ET.SubElement(xml_greeting, "did").text       = unicode(row.did)
            ET.SubElement(xml_greeting, "p_kd").text      = row.p_kd
            ET.SubElement(xml_greeting, "p_nm").text      = row.p_nm
            ET.SubElement(xml_greeting, "j_nm").text      = row.j_nm
            ET.SubElement(xml_greeting, "p1_nm").text     = row.p1_nm
            ET.SubElement(xml_greeting, "j1_nm").text     = row.j1_nm
            ET.SubElement(xml_greeting, "p2_nm").text     = row.p2_nm
            ET.SubElement(xml_greeting, "j2_nm").text     = row.j2_nm
            ET.SubElement(xml_greeting, "p3_nm").text     = row.p3_nm
            ET.SubElement(xml_greeting, "j3_nm").text     = row.j3_nm
            ET.SubElement(xml_greeting, "p4_nm").text     = row.p4_nm
            ET.SubElement(xml_greeting, "j4_nm").text     = row.j4_nm
            ET.SubElement(xml_greeting, "p5_nm").text     = row.p5_nm
            ET.SubElement(xml_greeting, "j5_nm").text     = row.j5_nm
            
            # Untuk menampilkan nama pengirim dan jabatannya sesuai create_uid
            #a = DBSession.query(Pegawai.kode.label('p_kd'),
            #                    Pegawai.nama.label('p_nm'), 
            #                    Jabatan.nama.label('j_nm')
            #            ).filter(Pegawai.user_id == row.uid,
            #                     Pegawai.jabatan_id == Jabatan.id,							
            #            )
            #for row1 in a :
            #    ET.SubElement(xml_greeting, "p_kd").text  = unicode(row1.p_kd)
            #    ET.SubElement(xml_greeting, "p_nm").text  = unicode(row1.p_nm)
            #    ET.SubElement(xml_greeting, "j_nm").text  = unicode(row1.j_nm)
        return self.root
        
# Surat Masuk/Disposisi (to_uid) #
class surat_masuk_Generator(JasperGenerator):
    def __init__(self):
        super(surat_masuk_Generator, self).__init__()
        self.reportname = get_rpath('Surat_masuk.jrxml')
        self.xpath = '/surat/surat_masuk'
        self.root = ET.Element('surat') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'surat_masuk')
            ET.SubElement(xml_greeting, "surat_ft").text    = row.surat_ft
            ET.SubElement(xml_greeting, "surat_nm").text    = row.surat_nm
            ET.SubElement(xml_greeting, "surat_ns").text    = row.surat_ns
            ET.SubElement(xml_greeting, "dis_t").text       = unicode(row.dis_t)
            ET.SubElement(xml_greeting, "dis_n").text       = row.dis_n
            ET.SubElement(xml_greeting, "dis_nf").text      = row.dis_nf
            if row.dis_df == None:
                row.dis_df = ''
            print '-----------------date feedback-----------------',row.dis_df
            ET.SubElement(xml_greeting, "dis_df").text      = unicode(row.dis_df)
            ET.SubElement(xml_greeting, "dis_s").text       = row.dis_s
            ET.SubElement(xml_greeting, "dis_j").text       = unicode(row.dis_j)
            
            b = DBSession.query(Job.nama.label('job_nm'),
                            ).filter(Job.id == row.dis_j,							
                            )
            for row1 in b :
                ET.SubElement(xml_greeting, "job_nm").text  = unicode(row1.job_nm)
			
        return self.root
     
# Surat Masuk/Disposisi (all) #
class surat_masuk_all_Generator(JasperGenerator):
    def __init__(self):
        super(surat_masuk_all_Generator, self).__init__()
        self.reportname = get_rpath('Surat_masuk_all.jrxml')
        self.xpath = '/surat/surat_masuk_all'
        self.root = ET.Element('surat') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'surat_masuk_all')
            ET.SubElement(xml_greeting, "surat_ft").text    = row.surat_ft
            ET.SubElement(xml_greeting, "surat_nm").text    = row.surat_nm
            ET.SubElement(xml_greeting, "surat_ns").text    = row.surat_ns
            ET.SubElement(xml_greeting, "dis_t").text       = unicode(row.dis_t)
            ET.SubElement(xml_greeting, "dis_n").text       = row.dis_n
            ET.SubElement(xml_greeting, "dis_nf").text      = row.dis_nf
            if row.dis_df == None:
                row.dis_df = ''
            print '-----------------date feedback-----------------',row.dis_df
            ET.SubElement(xml_greeting, "dis_df").text      = unicode(row.dis_df)
            ET.SubElement(xml_greeting, "dis_s").text       = row.dis_s
            ET.SubElement(xml_greeting, "dis_j").text       = unicode(row.dis_j)
            
            b = DBSession.query(Job.nama.label('job_nm'),
                            ).filter(Job.id == row.dis_j,							
                            )
            for row1 in b :
                ET.SubElement(xml_greeting, "job_nm").text  = unicode(row1.job_nm)
			
        return self.root
        
# Surat Keluar/Disposisi (from_uid) #
class surat_keluar_Generator(JasperGenerator):
    def __init__(self):
        super(surat_keluar_Generator, self).__init__()
        self.reportname = get_rpath('Surat_keluar.jrxml')
        self.xpath = '/surat/surat_keluar'
        self.root = ET.Element('surat') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'surat_keluar')
            ET.SubElement(xml_greeting, "surat_ft").text    = row.surat_ft
            ET.SubElement(xml_greeting, "surat_nm").text    = row.surat_nm
            ET.SubElement(xml_greeting, "surat_ns").text    = row.surat_ns
            ET.SubElement(xml_greeting, "dis_t").text       = unicode(row.dis_t)
            ET.SubElement(xml_greeting, "dis_n").text       = row.dis_n
            ET.SubElement(xml_greeting, "dis_nf").text      = row.dis_nf
            if row.dis_df == None:
                row.dis_df = ''
            print '-----------------date feedback-----------------',row.dis_df
            ET.SubElement(xml_greeting, "dis_df").text      = unicode(row.dis_df)
            ET.SubElement(xml_greeting, "dis_s").text       = row.dis_s
            ET.SubElement(xml_greeting, "dis_j").text       = unicode(row.dis_j)
            
            b = DBSession.query(Job.nama.label('job_nm'),
                            ).filter(Job.id == row.dis_j,							
                            )
            for row1 in b :
                ET.SubElement(xml_greeting, "job_nm").text  = unicode(row1.job_nm)
			
        return self.root
     
# Surat Keluar/Disposisi (all) #
class surat_keluar_all_Generator(JasperGenerator):
    def __init__(self):
        super(surat_keluar_all_Generator, self).__init__()
        self.reportname = get_rpath('Surat_keluar_all.jrxml')
        self.xpath = '/surat/surat_keluar_all'
        self.root = ET.Element('surat') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'surat_keluar_all')
            ET.SubElement(xml_greeting, "surat_ft").text    = row.surat_ft
            ET.SubElement(xml_greeting, "surat_nm").text    = row.surat_nm
            ET.SubElement(xml_greeting, "surat_ns").text    = row.surat_ns
            ET.SubElement(xml_greeting, "dis_t").text       = unicode(row.dis_t)
            ET.SubElement(xml_greeting, "dis_n").text       = row.dis_n
            ET.SubElement(xml_greeting, "dis_nf").text      = row.dis_nf
            if row.dis_df == None:
                row.dis_df = ''
            print '-----------------date feedback-----------------',row.dis_df
            ET.SubElement(xml_greeting, "dis_df").text      = unicode(row.dis_df)
            ET.SubElement(xml_greeting, "dis_s").text       = row.dis_s
            ET.SubElement(xml_greeting, "dis_j").text       = unicode(row.dis_j)
            
            b = DBSession.query(Job.nama.label('job_nm'),
                            ).filter(Job.id == row.dis_j,							
                            )
            for row1 in b :
                ET.SubElement(xml_greeting, "job_nm").text  = unicode(row1.job_nm)
			
        return self.root
        
# Laporan Surat Baru #
class surat_laporan_Generator(JasperGenerator):
    def __init__(self):
        super(surat_laporan_Generator, self).__init__()
        self.reportname = get_rpath('Laporan_surat_baru.jrxml')
        self.xpath = '/surat/surat_baru_lap'
        self.root = ET.Element('surat') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'surat_baru_lap')
            ET.SubElement(xml_greeting, "surat_kd").text  = row.surat_kd
            ET.SubElement(xml_greeting, "surat_ft").text  = row.surat_ft
            ET.SubElement(xml_greeting, "surat_nm").text  = row.surat_nm
            ET.SubElement(xml_greeting, "surat_ns").text  = row.surat_ns
            ET.SubElement(xml_greeting, "surat_ts").text  = unicode(row.surat_ts)
            ET.SubElement(xml_greeting, "surat_tt").text  = unicode(row.surat_tt)
            ET.SubElement(xml_greeting, "surat_sf").text  = row.surat_sf
            ET.SubElement(xml_greeting, "surat_a").text   = row.surat_a
            ET.SubElement(xml_greeting, "surat_s").text   = row.surat_s
            ET.SubElement(xml_greeting, "surat_i").text   = row.surat_i
            ET.SubElement(xml_greeting, "surat_l").text   = row.surat_l
        return self.root
     
# Laporan Surat Masuk #
class surat2_laporan_Generator(JasperGenerator):
    def __init__(self):
        super(surat2_laporan_Generator, self).__init__()
        self.reportname = get_rpath('Laporan_surat_masuk.jrxml')
        self.xpath = '/surat/surat_masuk_lap'
        self.root = ET.Element('surat') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'surat_masuk_lap')
            ET.SubElement(xml_greeting, "surat_ft").text    = row.surat_ft
            ET.SubElement(xml_greeting, "surat_nm").text    = row.surat_nm
            ET.SubElement(xml_greeting, "surat_ns").text    = row.surat_ns
            ET.SubElement(xml_greeting, "dis_t").text       = unicode(row.dis_t)
            ET.SubElement(xml_greeting, "dis_n").text       = row.dis_n
            ET.SubElement(xml_greeting, "dis_nf").text      = row.dis_nf
            if row.dis_df == None:
                row.dis_df = ''
            print '-----------------date feedback-----------------',row.dis_df
            ET.SubElement(xml_greeting, "dis_df").text      = unicode(row.dis_df)
            ET.SubElement(xml_greeting, "dis_s").text       = row.dis_s
            ET.SubElement(xml_greeting, "dis_j").text       = unicode(row.dis_j)
            
            b = DBSession.query(Job.nama.label('job_nm'),
                            ).filter(Job.id == row.dis_j,							
                            )
            for row1 in b :
                ET.SubElement(xml_greeting, "job_nm").text  = unicode(row1.job_nm)
			
        return self.root
     
# Laporan Surat Keluar #
class surat3_laporan_Generator(JasperGenerator):
    def __init__(self):
        super(surat3_laporan_Generator, self).__init__()
        self.reportname = get_rpath('Laporan_surat_keluar.jrxml')
        self.xpath = '/surat/surat_keluar_lap'
        self.root = ET.Element('surat') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'surat_keluar_lap')
            ET.SubElement(xml_greeting, "surat_ft").text    = row.surat_ft
            ET.SubElement(xml_greeting, "surat_nm").text    = row.surat_nm
            ET.SubElement(xml_greeting, "surat_ns").text    = row.surat_ns
            ET.SubElement(xml_greeting, "dis_t").text       = unicode(row.dis_t)
            ET.SubElement(xml_greeting, "dis_n").text       = row.dis_n
            ET.SubElement(xml_greeting, "dis_nf").text      = row.dis_nf
            if row.dis_df == None:
                row.dis_df = ''
            print '-----------------date feedback-----------------',row.dis_df
            ET.SubElement(xml_greeting, "dis_df").text      = unicode(row.dis_df)
            ET.SubElement(xml_greeting, "dis_s").text       = row.dis_s
            ET.SubElement(xml_greeting, "dis_j").text       = unicode(row.dis_j)
            
            b = DBSession.query(Job.nama.label('job_nm'),
                            ).filter(Job.id == row.dis_j,							
                            )
            for row1 in b :
                ET.SubElement(xml_greeting, "job_nm").text  = unicode(row1.job_nm)
			
        return self.root

###############################		
## Khusus untuk modul master ##
###############################						

# Master Pegawai #
class master_pegawai_Generator(JasperGenerator):
    def __init__(self):
        super(master_pegawai_Generator, self).__init__()
        self.reportname = get_rpath('Master_pegawai.jrxml')
        self.xpath = '/surat/pegawai'
        self.root = ET.Element('surat') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'pegawai')
            ET.SubElement(xml_greeting, "id1").text            = unicode(row.id1)
            ET.SubElement(xml_greeting, "pegawai_kd").text     = row.pegawai_kd
            ET.SubElement(xml_greeting, "pegawai_nm").text     = row.pegawai_nm
            ET.SubElement(xml_greeting, "unit_nm").text        = row.unit_nm
            ET.SubElement(xml_greeting, "jabatan_nm").text     = row.jabatan_nm
            ET.SubElement(xml_greeting, "email").text          = row.email
            ET.SubElement(xml_greeting, "handphone").text      = row.handphone
            ET.SubElement(xml_greeting, "alamat").text         = row.alamat
			
            b = DBSession.query(User.user_name.label('user_nm'),
                            ).filter(User.id == row.id1,							
                            )
            for row1 in b :
                ET.SubElement(xml_greeting, "user_nm").text  = unicode(row1.user_nm)

        return self.root		
		
# Master Pegawai All#
class master_pegawai2_Generator(JasperGenerator):
    def __init__(self):
        super(master_pegawai2_Generator, self).__init__()
        self.reportname = get_rpath('Master_pegawai_all.jrxml')
        self.xpath = '/surat/pegawai_all'
        self.root = ET.Element('surat') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'pegawai_all')
            ET.SubElement(xml_greeting, "id1").text            = unicode(row.id1)
            ET.SubElement(xml_greeting, "pegawai_kd").text     = row.pegawai_kd
            ET.SubElement(xml_greeting, "pegawai_nm").text     = row.pegawai_nm
            ET.SubElement(xml_greeting, "unit_nm").text        = row.unit_nm
            ET.SubElement(xml_greeting, "jabatan_nm").text     = row.jabatan_nm
            ET.SubElement(xml_greeting, "email").text          = row.email
            ET.SubElement(xml_greeting, "handphone").text      = row.handphone
            ET.SubElement(xml_greeting, "alamat").text         = row.alamat
			
            b = DBSession.query(User.user_name.label('user_nm'),
                            ).filter(User.id == row.id1,							
                            )
            for row1 in b :
                ET.SubElement(xml_greeting, "user_nm").text  = unicode(row1.user_nm)

        return self.root		
		
# Master Jabatan #
class master_jabatan_Generator(JasperGenerator):
    def __init__(self):
        super(master_jabatan_Generator, self).__init__()
        self.reportname = get_rpath('Master_jabatan.jrxml')
        self.xpath = '/surat/jabatan'
        self.root = ET.Element('surat') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'jabatan')
            ET.SubElement(xml_greeting, "id1").text            = unicode(row.id1)
            ET.SubElement(xml_greeting, "jabatan_kd").text     = row.jabatan_kd
            ET.SubElement(xml_greeting, "jabatan_nm").text     = row.jabatan_nm
			
            b = DBSession.query(Jabatan.nama.label('header_nm'),
                            ).filter(Jabatan.id == row.id1,							
                            )
            for row1 in b :
                ET.SubElement(xml_greeting, "header_nm").text  = unicode(row1.header_nm)

        return self.root			

# Master Jabatan All #
class master_jabatan2_Generator(JasperGenerator):
    def __init__(self):
        super(master_jabatan2_Generator, self).__init__()
        self.reportname = get_rpath('Master_jabatan_all.jrxml')
        self.xpath = '/surat/jabatan_all'
        self.root = ET.Element('surat') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'jabatan_all')
            ET.SubElement(xml_greeting, "id1").text            = unicode(row.id1)
            ET.SubElement(xml_greeting, "jabatan_kd").text     = row.jabatan_kd
            ET.SubElement(xml_greeting, "jabatan_nm").text     = row.jabatan_nm
			
            b = DBSession.query(Jabatan.nama.label('header_nm'),
                            ).filter(Jabatan.id == row.id1,							
                            )
            for row1 in b :
                ET.SubElement(xml_greeting, "header_nm").text  = unicode(row1.header_nm)

        return self.root

# Master Pekerjaan #
class master_job_Generator(JasperGenerator):
    def __init__(self):
        super(master_job_Generator, self).__init__()
        self.reportname = get_rpath('Master_job.jrxml')
        self.xpath = '/surat/job'
        self.root = ET.Element('surat') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'job')
            ET.SubElement(xml_greeting, "job_kd").text     = row.job_kd
            ET.SubElement(xml_greeting, "job_nm").text     = row.job_nm
        return self.root

# Master Pekerjaan All #
class master_job2_Generator(JasperGenerator):
    def __init__(self):
        super(master_job2_Generator, self).__init__()
        self.reportname = get_rpath('Master_job_all.jrxml')
        self.xpath = '/surat/job_all'
        self.root = ET.Element('surat') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'job_all')
            ET.SubElement(xml_greeting, "job_kd").text     = row.job_kd
            ET.SubElement(xml_greeting, "job_nm").text     = row.job_nm
        return self.root
				
# Master Urusan #
class master_urusan_Generator(JasperGenerator):
    def __init__(self):
        super(master_urusan_Generator, self).__init__()
        self.reportname = get_rpath('Master_urusan.jrxml')
        self.xpath = '/surat/urusan'
        self.root = ET.Element('surat') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'urusan')
            ET.SubElement(xml_greeting, "urusan_kd").text     = row.urusan_kd
            ET.SubElement(xml_greeting, "urusan_nm").text     = row.urusan_nm
        return self.root	
		
# Master Urusan All #
class master_urusan2_Generator(JasperGenerator):
    def __init__(self):
        super(master_urusan2_Generator, self).__init__()
        self.reportname = get_rpath('Master_urusan_all.jrxml')
        self.xpath = '/surat/urusan_all'
        self.root = ET.Element('surat') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'urusan_all')
            ET.SubElement(xml_greeting, "urusan_kd").text     = row.urusan_kd
            ET.SubElement(xml_greeting, "urusan_nm").text     = row.urusan_nm
        return self.root					

# Master Unit Kerja #
class master_unit_Generator(JasperGenerator):
    def __init__(self):
        super(master_unit_Generator, self).__init__()
        self.reportname = get_rpath('Master_unit.jrxml')
        self.xpath = '/surat/uniker'
        self.root = ET.Element('surat') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'uniker')
            ET.SubElement(xml_greeting, "id1").text            = unicode(row.id1)
            ET.SubElement(xml_greeting, "unit_kd").text        = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text        = row.unit_nm
            ET.SubElement(xml_greeting, "urusan_kd").text      = row.urusan_kd
            ET.SubElement(xml_greeting, "urusan_nm").text      = row.urusan_nm
            ET.SubElement(xml_greeting, "level_id").text       = unicode(row.level_id)
			
            b = DBSession.query(Unit.nama.label('header_nm'),
                            ).filter(Unit.id == row.id1,							
                            )
            for row1 in b :
                ET.SubElement(xml_greeting, "header_nm").text  = unicode(row1.header_nm)

        return self.root			

# Master Unit Kerja All #
class master_unit2_Generator(JasperGenerator):
    def __init__(self):
        super(master_unit2_Generator, self).__init__()
        self.reportname = get_rpath('Master_unit_all.jrxml')
        self.xpath = '/surat/uniker_all'
        self.root = ET.Element('surat') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'uniker_all')
            ET.SubElement(xml_greeting, "id1").text            = unicode(row.id1)
            ET.SubElement(xml_greeting, "unit_kd").text        = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text        = row.unit_nm
            ET.SubElement(xml_greeting, "urusan_kd").text      = row.urusan_kd
            ET.SubElement(xml_greeting, "urusan_nm").text      = row.urusan_nm
            ET.SubElement(xml_greeting, "level_id").text       = unicode(row.level_id)
			
            b = DBSession.query(Unit.nama.label('header_nm'),
                            ).filter(Unit.id == row.id1,							
                            )
            for row1 in b :
                ET.SubElement(xml_greeting, "header_nm").text  = unicode(row1.header_nm)

        return self.root		