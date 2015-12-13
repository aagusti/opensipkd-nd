import os
from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Date,
    SmallInteger,
    BigInteger,
    ForeignKey,
    UniqueConstraint,
    func,
    extract,
    case
    )
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
    relationship,
    backref
    )
from sqlalchemy.sql.functions import concat
from ..models import (
    Base,
    DefaultModel,
    osBaseModel,
    osExtendModel,
    User
    )
from ..models.pemda import (
    Unit, Urusan, UserUnit
    )
from ..tools import (
    create_now, get_settings,
    )

## Pekerjaan ##
class Job(Base, osExtendModel):
    __tablename__  = 'jobs'
    __table_args__ = {'extend_existing':True, 'schema' : 'notadinas',} 
	
## Pegawai ##
class Pegawai(Base, osExtendModel):
    __tablename__  = 'pegawais'
    __table_args__ = {'extend_existing':True, 'schema' : 'notadinas',}   
    
    unit_id    = Column(Integer,  ForeignKey("pemda.units.id"),        nullable=False)
    user_id    = Column(Integer,  nullable=True) #ForeignKey("users.id"),              
    jabatan_id = Column(Integer,  ForeignKey("notadinas.jabatans.id"), nullable=False)
    email      = Column(String(100))
    handphone  = Column(String(20))
    alamat     = Column(String(255))
	
    units      = relationship("Unit",    backref=backref('pegawais'))
    jabatans   = relationship("Jabatan", backref=backref('pegawais'))
    #users      = relationship("User",    backref=backref('pegawais'))

## Jabatan ##
class Jabatan(Base, osExtendModel):
    __tablename__  = 'jabatans'
    __table_args__ = {'extend_existing':True, 'schema' : 'notadinas',} 
	
    id        = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey("notadinas.jabatans.id"), nullable=True)	
	
    parent    = relationship("Jabatan", backref=backref('jabatans'), remote_side=[id])
	
## Surat ##
class Surat(Base, osExtendModel):
    __tablename__  = 'surats'
    __table_args__ = {'extend_existing':True, 'schema' : 'notadinas',} 
	
    from_to        = Column(String(30))
    no_surat       = Column(String(30))
    tanggal_surat  = Column(DateTime)
    tanggal_terima = Column(DateTime)
    jenis          = Column(SmallInteger, nullable=False, default=1) ## 1 'Surat Masuk' , 2 'Surat Keluar' ##
    sifat          = Column(SmallInteger, nullable=False, default=0) ## 0 'Biasa' , 1 'Segera' , 2 'Sangat Segera' , 3 'Rahasia' ##
    indeks         = Column(String(30))
    agenda         = Column(String(30))
    lampiran       = Column(String(100))
    status         = Column(SmallInteger, nullable=False, default=0) ## 0 'Masuk' , 1 'Keluar' , 2 'Diteruskan' ##

## Surat Detail ## 
class SuratDetail(Base, DefaultModel):
    __tablename__  = 'surat_details'
    __table_args__ = {'extend_existing':True, 'schema' : 'notadinas',}
	
    surat_id    = Column(Integer, ForeignKey("notadinas.surats.id"), nullable=False)
    path        = Column(String(255), nullable=False, unique=True)
    name        = Column(String(255), nullable=False) # original filename
    mime        = Column(String(255), nullable=False) # file type
    size        = Column(Integer,     nullable=False) # byte
    user_id     = Column(Integer)
	
    surats      = relationship("Surat", backref=backref('surat_details'))	
	
    def fullpath(self):
        settings = get_settings()
        dir_path = os.path.realpath(settings['static_files'])         
        return os.path.join(dir_path, self.path)
		
## Penerima Surat ## 
class PenerimaSurat(Base, DefaultModel):
    __tablename__  = 'penerima_surats'
    __table_args__ = {'extend_existing':True, 'schema' : 'notadinas',}
	
    surat_id       = Column(Integer, ForeignKey("notadinas.surats.id"),   nullable=False)
    pegawai_id     = Column(Integer, ForeignKey("notadinas.pegawais.id"), nullable=False)
    user_id        = Column(Integer, nullable=True)             
    tanggal        = Column(DateTime)	
    disabled       = Column(SmallInteger, nullable=False, default=0)  
	
    surats         = relationship("Surat",   backref=backref('penerima_surats'))	
    pegawais       = relationship("Pegawai", backref=backref('penerima_surats'))	
	
## Disposisi ##
class Disposisi(Base, osBaseModel):
    __tablename__  = 'disposisis'
    __table_args__ = {'extend_existing':True, 'schema' : 'notadinas',} 
	
    tanggal        = Column(DateTime)
    surat_id       = Column(Integer, ForeignKey("notadinas.surats.id"), nullable=False)
    from_uid       = Column(Integer) 
    to_uid         = Column(Integer) 
    notes          = Column(String(255))
    job_id         = Column(Integer, nullable=True) #, ForeignKey("notadinas.jobs.id"),   nullable=False)
    need_feedback  = Column(SmallInteger, nullable=False, default=0) ## 0 'Tidak' , 1 'Ya' ##
    date_feedback  = Column(DateTime)
    status         = Column(SmallInteger, nullable=False, default=0) ## 0 'Unread' , 1 'Read', 2 'Diteruskan' ##
    dis_id         = Column(Integer, default=0)
	
    surats         = relationship("Surat", backref=backref('disposisis'))	
    #jobs           = relationship("Job",   backref=backref('disposisis'))	
	
## Disposisi Komentar ## 
class DisposisiComment(Base, DefaultModel):
    __tablename__  = 'disposisi_comments'
    __table_args__ = {'extend_existing':True, 'schema' : 'notadinas',}
	
    disposisi_id = Column(Integer, ForeignKey("notadinas.disposisis.id"), nullable=False)
    komentar     = Column(String(255))
    user_id      = Column(Integer, nullable=True)
	
    disposisis   = relationship("Disposisi", backref=backref('disposisi_comments'))	

## Penerima Disposisi ## 
class PenerimaDisposisi(Base, DefaultModel):
    __tablename__  = 'penerima_disposisis'
    __table_args__ = {'extend_existing':True, 'schema' : 'notadinas',}
	
    disposisi_id   = Column(Integer, ForeignKey("notadinas.disposisis.id"), nullable=False)
    pegawai_id     = Column(Integer, ForeignKey("notadinas.pegawais.id"),   nullable=False)
    user_id        = Column(Integer, nullable=True)             
    tanggal        = Column(DateTime)	
    disabled       = Column(SmallInteger, nullable=False, default=0)  
	
    disposisis     = relationship("Disposisi", backref=backref('penerima_disposisis'))	
    pegawais       = relationship("Pegawai",   backref=backref('penerima_disposisis'))	