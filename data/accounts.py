import sqlalchemy as sa
from .__db_session import SqlAlchemyBase


class Accounts(SqlAlchemyBase):
    __tablename__ = 'accounts'

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    user = sa.Column(sa.Integer, sa.ForeignKey("users.id"))
    type = sa.Column(sa.String, default='income')
    category = sa.Column(sa.String, default='salary')
    date = sa.Column(sa.Date)
    amount = sa.Column(sa.Numeric, default=0)

    def __str__(self) -> str:
        return f'{self.id}'

    def __repr__(self) -> str:
        return self.__str__()
