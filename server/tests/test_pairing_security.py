import datetime
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.common.database import Base, connect_args
from app.modules.pairings.enums import PairingStatusEnum
from app.modules.pairings.models import PairingModel
from app.modules.pairings.repository import PairingsRepository
from app.modules.pairings.service import PairingsService


@pytest.fixture
def pairing_db(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path}/pairing.db", connect_args=connect_args
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    with factory() as db:
        # Isolate pairing claims from unrelated role/user setup.
        db.execute(text("PRAGMA foreign_keys=OFF"))
        db.add(
            PairingModel(
                id="pair",
                user_code="1234",
                device_code="device",
                expires_at=datetime.datetime.now() + datetime.timedelta(minutes=10),
            )
        )
        db.commit()
    yield factory
    engine.dispose()


def test_linked_pairing_cannot_be_reassigned(pairing_db):
    with pairing_db() as db:
        db.execute(text("PRAGMA foreign_keys=OFF"))
        service = PairingsService(PairingsRepository(db))
        service.authorize_pairing_code("1234", MagicMock(id="first"))
        db.commit()
        with pytest.raises(HTTPException) as error:
            service.authorize_pairing_code("1234", MagicMock(id="second"))
        assert error.value.status_code == 409
        db.commit()
        pairing = db.get(PairingModel, "pair")
        assert pairing.user_id == "first"
        assert pairing.status == PairingStatusEnum.LINKED


def test_concurrent_claims_have_exactly_one_winner(pairing_db):
    def claim(user):
        with pairing_db() as db:
            db.execute(text("PRAGMA foreign_keys=OFF"))
            result = PairingsRepository(db).authorize_pending("pair", user)
            db.commit()
            return result

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(claim, ["first", "second"])) == [False, True]


def test_expired_pairing_cannot_be_claimed(pairing_db):
    with pairing_db() as db:
        pairing = db.get(PairingModel, "pair")
        pairing.expires_at = datetime.datetime.now() - datetime.timedelta(seconds=1)
        db.commit()
        assert not PairingsRepository(db).authorize_pending("pair", "user")


def test_pairing_keeps_four_digit_protocol_with_secure_randomness(monkeypatch):
    repo = MagicMock()
    repo.find_by_user_code.return_value = None
    choice = MagicMock(return_value="7")
    monkeypatch.setattr("app.modules.pairings.service.secrets.choice", choice)
    result = PairingsService(repo).generate_pairing_codes()
    assert result.user_code == "7777"
    assert choice.call_count == 4
