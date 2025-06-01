# backend/tests/unit/test_models.py
from .. import db
from ...app.models import User, ClientCall # 테스트할 모델 임포트
from datetime import datetime, timezone

def test_new_user(db): # db fixture 사용
    """새로운 User 객체가 올바르게 생성되는지 테스트합니다."""
    user = User(username='testuser', name='Test User', status='available')
    user.password_hash = 'hashed_password' # 실제로는 set_password 메서드 사용 권장
    # user.set_password('password123') # 모델에 set_password 메서드가 있다면

    db.session.add(user)
    db.session.commit()

    retrieved_user = User.query.filter_by(username='testuser').first()
    assert retrieved_user is not None
    assert retrieved_user.name == 'Test User'
    assert retrieved_user.status == 'available'
    # assert check_password_hash(retrieved_user.password_hash, 'password123') # set_password 사용 시

def test_new_client_call(db):
    """새로운 ClientCall 객체가 올바르게 생성되는지 테스트합니다."""
    # 테스트를 위해 User 객체 먼저 생성
    counselor = User(username='counselor', name='Counselor', status='available')
    counselor.password_hash = 'test'
    db.session.add(counselor)
    db.session.commit()

    call = ClientCall(
        phone_number='01012345678',
        audio_file_path='/path/to/audio.wav',
        risk_level=1,
        status='available_for_assignment',
        assigned_counselor_id=counselor.id
    )
    db.session.add(call)
    db.session.commit()

    retrieved_call = ClientCall.query.filter_by(phone_number='01012345678').first()
    assert retrieved_call is not None
    assert retrieved_call.risk_level == 1
    assert retrieved_call.assigned_counselor_id == counselor.id

def test_user_password():
    user = User(username='testuser', name='Test User')
    user.set_password('password123')
    assert user.check_password('password123')
    assert not user.check_password('wrongpassword')