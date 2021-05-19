from typing import Optional

from sqlalchemy import BigInteger, Boolean, Column, ForeignKey, String, Integer
from sqlalchemy.orm import relationship

from database import database
from database import session


class ACL_group(database.base):
    __tablename__ = "acl_groups"

    id = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(BigInteger)
    name = Column(String)
    parent = Column(String, default=None)
    role_id = Column(BigInteger, default=None)
    rules = relationship("ACL_rule_group", back_populates="group")

    def __repr__(self):
        return (
            f'<ACL_group id="{self.id}" name="{self.name}" parent="{self.parent}"'
            f'guild_id="{self.guild_id}" role_id="{self.role_id}">'
        )

    def __eq__(self, obj):
        return type(self) == type(obj) and self.guild_id == obj.guild_id and self.name == obj.name

    def to_dict(self):
        return {
            "guild_id": self.guild_id,
            "name": self.name,
            "parent": self.parent,
            "role_id": self.role_id,
        }

    @staticmethod
    def get(guild_id: int, name: str):
        query = session.query(ACL_group).filter_by(guild_id=guild_id, name=name).one_or_none()
        return query

    @staticmethod
    def get_by_role(guild_id: int, role_id: int):
        query = session.query(ACL_group).filter_by(guild_id=guild_id, role_id=role_id).one_or_none()
        return query

    @staticmethod
    def get_all(guild_id: int):
        query = session.query(ACL_group).all()
        return query

    @staticmethod
    def add(guild_id: int, name: str, parent: Optional[str], role_id: Optional[int]):
        # check that the parent exists
        if parent is not None and ACL_group.get(guild_id, parent) is None:
            raise ValueError("Invalid ACL parent group.")

        group = ACL_group(guild_id=guild_id, name=name, parent=parent, role_id=role_id)

        session.merge(group)
        session.commit()
        return group

    def save(self):
        session.commit()

    @staticmethod
    def remove(guild_id: int, name: str):
        query = session.query(ACL_group).filter_by(guild_id=guild_id, name=name).delete()
        return query


class ACL_rule(database.base):
    __tablename__ = "acl_rules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(BigInteger)
    command = Column(String)
    default = Column(Boolean, default=False)
    users = relationship("ACL_rule_user", back_populates="rule")
    groups = relationship("ACL_rule_group", back_populates="rule")

    def __repr__(self):
        return (
            f'<ACL_rule id="{self.id}" guild_id="{self.guild_id}" '
            f'command="{self.command}" default="{self.default}">'
        )

    def __eq__(self, obj):
        return type(self) == type(obj) and self.id == obj.id

    def to_dict(self):
        return {
            "id": self.id,
            "guild_id": self.id,
            "command": self.command,
            "default": self.default,
        }


class ACL_rule_user(database.base):
    __tablename__ = "acl_rule_users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    rule_id = Column(Integer, ForeignKey("acl_rules.id", ondelete="CASCADE"))
    rule = relationship("ACL_rule", back_populates="users")
    user_id = Column(BigInteger)
    allow = Column(Boolean)

    def __repr__(self):
        return (
            f'<ACL_rule_user id="{self.id}" '
            f'rule_id="{self.rule_id}" user_id="{self.user_id}" '
            f'allow="{self.allow}">'
        )

    def __eq__(self, obj):
        return type(self) == type(obj) and self.id == obj.id

    def to_dict(self):
        return {
            "id": self.id,
            "rule_id": self.rule_id,
            "user_id": self.user_id,
            "allow": self.allow,
        }


class ACL_rule_group(database.base):
    __tablename__ = "acl_rule_groups"

    id = Column(Integer, primary_key=True, autoincrement=True)
    rule_id = Column(Integer, ForeignKey("acl_rules.id", ondelete="CASCADE"))
    rule = relationship("ACL_rule", back_populates="groups")
    group_id = Column(Integer, ForeignKey("acl_groups.id", ondelete="CASCADE"))
    group = relationship("ACL_group", back_populates="rules")
    allow = Column(Boolean, default=None)

    def __repr__(self):
        return (
            f'<ACL_rule_group id="{self.id}" '
            f'rule_id="{self.rule_id}" group_id="{self.group_id}" '
            f'allow="{self.allow}">'
        )

    def __eq__(self, obj):
        return type(self) == type(obj) and self.id == obj.id

    def to_dict(self):
        return {
            "id": self.id,
            "rule_id": self.rule_id,
            "group_id": self.group_id,
            "allow": self.allow,
        }