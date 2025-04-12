from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.file import File
from app.models.user import User

class FileRepository:
    """文件存储库"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_file(
        self,
        user_id: int,
        original_filename: str,
        stored_filename: str,
        file_path: str,
        file_type: str,
        content_type: str,
        file_size: int
    ) -> File:
        """创建新的文件记录"""
        file_obj = File(
            user_id=user_id,
            original_filename=original_filename,
            stored_filename=stored_filename,
            file_path=file_path,
            file_type=file_type,
            content_type=content_type,
            file_size=file_size
        )
        self.db.add(file_obj)
        self.db.commit()
        self.db.refresh(file_obj)
        return file_obj
    
    def get_file_by_id(self, file_id: int) -> Optional[File]:
        """通过ID获取文件"""
        return self.db.query(File).filter(File.id == file_id).first()
    
    def get_file_by_stored_filename(self, stored_filename: str) -> Optional[File]:
        """通过存储文件名获取文件"""
        return self.db.query(File).filter(File.stored_filename == stored_filename).first()
    
    def get_files_by_user_id(self, user_id: int) -> List[File]:
        """获取用户的所有文件"""
        return self.db.query(File).filter(File.user_id == user_id).order_by(File.created_at.desc()).all()
    
    def get_files_by_user_and_type(self, user_id: int, file_type: str) -> List[File]:
        """获取用户的特定类型文件"""
        return self.db.query(File).filter(
            File.user_id == user_id,
            File.file_type == file_type
        ).order_by(File.created_at.desc()).all()
    
    def delete_file(self, file_id: int) -> bool:
        """删除文件记录"""
        file = self.get_file_by_id(file_id)
        if not file:
            return False
        
        self.db.delete(file)
        self.db.commit()
        return True 