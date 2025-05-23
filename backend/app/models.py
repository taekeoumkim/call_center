# backend/app/models.py
from . import db # app/__init__.py 에서 생성된 db 객체를 가져옴
from datetime import datetime, timezone

class User(db.Model): # 예시 모델, 실제 모델명으로 대체
    __tablename__ = 'users' # 테이블명 명시 권장
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False) # 해시된 비밀번호 저장
    name = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default='offline', nullable=False) # 'offline', 'available', 'busy'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 비밀번호 설정 및 확인 메서드 (선택 사항이지만 권장)
    # def set_password(self, password):
    #     self.password_hash = generate_password_hash(password)
    #
    # def check_password(self, password):
    #     return check_password_hash(self.password_hash, password)

    # 관계 설정 (예: 상담사가 작성한 소견서들)
    # reports_authored = db.relationship('ConsultationReport', backref='author', lazy=True, foreign_keys='ConsultationReport.counselor_id')

    def __repr__(self):
        return f'<User {self.username}>'

class ClientCall(db.Model):
    __tablename__ = 'client_calls'
    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(20), nullable=False)
    audio_file_path = db.Column(db.String(255))
    risk_level = db.Column(db.Integer, default=0) # 0: unassigned, 1: low, 2: medium, 3: high
    status = db.Column(db.String(20), default='pending', nullable=False) # 'pending', 'assigned', 'completed'
    assigned_counselor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    received_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 관계 설정 (예: 이 통화에 배정된 상담사)
    # counselor = db.relationship('User', backref=db.backref('assigned_calls', lazy=True))
    # 관계 설정 (예: 이 통화에 대한 소견서)
    # report = db.relationship('ConsultationReport', backref='client_call_origin', uselist=False, lazy=True) # 하나의 통화는 하나의 소견서를 가질 수 있음 (가정)

    def __repr__(self):
        return f'<ClientCall {self.id} - {self.phone_number}>'

class ConsultationReport(db.Model):
    __tablename__ = 'consultation_reports'
    id = db.Column(db.Integer, primary_key=True)
    client_call_id = db.Column(db.Integer, db.ForeignKey('client_calls.id'), nullable=False, unique=True) # 하나의 통화에 하나의 리포트
    counselor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    client_name = db.Column(db.String(100))
    client_age = db.Column(db.Integer)
    client_gender = db.Column(db.String(10)) # 'male', 'female', 'other'
    memo_text = db.Column(db.Text)
    risk_level_recorded = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 관계 설정
    # authoring_counselor = db.relationship('User', backref=db.backref('consultation_reports', lazy=True), foreign_keys=[counselor_id])
    # originating_call = db.relationship('ClientCall', backref=db.backref('consultation_report', uselist=False, lazy=True), foreign_keys=[client_call_id])


    def __repr__(self):
        return f'<ConsultationReport {self.id} for ClientCall {self.client_call_id}>'
    
class TokenBlocklist(db.Model):
    __tablename__ = "token_blocklist"
    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(36), nullable=False, unique=True, index=True) # JWT ID
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)) # UTC 시간으로 저장

    def __repr__(self):
        return f"<TokenBlocklist {self.jti}>"