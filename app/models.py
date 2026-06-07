from sqlalchemy import Column, String, Integer, Float, DateTime, BigInteger
from app.database import Base


class Residential(Base):
    __tablename__ = "Residential"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    state = Column(String(100))
    city = Column(String(100))
    locality = Column(String(200))
    Sale_resale = Column(String(50))
    transactionType = Column(String(50))
    period = Column(String(10))
    noOfTrans = Column(Integer)
    weightageAvgValue = Column(Float)
    compensationInCr = Column(Float)
    chargeableSQFT = Column('chargeableSQFTInMillion', Float)
    crdt = Column(DateTime)


class Commercial(Base):
    __tablename__ = "Commercial"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    state = Column(String(100))
    city = Column(String(100))
    locality = Column(String(200))
    Sale_resale = Column(String(50))
    transactionType = Column(String(50))
    period = Column(String(10))
    noOfTrans = Column(Integer)
    weightageAvgValue = Column(Float)
    compensationInCr = Column(Float)
    chargeableSQFT = Column('chargeableSQFTInMillion', Float)
    crdt = Column(DateTime)


class CityAveragePrice(Base):
    __tablename__ = "cityAveragePrice"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    state = Column(String(100))
    city = Column(String(100))
    period = Column(String(10))
    transactionType = Column(String(50))
    avgPrice = Column(Float)
    totalTransactions = Column(Integer)
    totalValue = Column(Float)


class CityAveragePriceRent(Base):
    __tablename__ = "cityAveragePriceRent"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    state = Column(String(100))
    city = Column(String(100))
    period = Column(String(10))
    avgRent = Column(Float)
    totalTransactions = Column(Integer)


class TopDevelopers(Base):
    __tablename__ = "topDevelopers"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    developer = Column(String(200))
    city = Column(String(100))
    period = Column(String(10))
    totalTransactions = Column(Integer)
    totalValue = Column(Float)
    avgPrice = Column(Float)


class TopGainer(Base):
    __tablename__ = "topGainer"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    city = Column(String(100))
    period = Column(String(10))
    priceChange = Column(Float)
    percentChange = Column(Float)


class TopGainerByProject(Base):
    __tablename__ = "topGainerByProject"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    project = Column(String(200))
    developer = Column(String(200))
    city = Column(String(100))
    locality = Column(String(200))
    period = Column(String(10))
    priceChange = Column(Float)
    percentChange = Column(Float)
    totalTransactions = Column(Integer)


class TopGainerRent(Base):
    __tablename__ = "topGainerRent"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    city = Column(String(100))
    period = Column(String(10))
    rentChange = Column(Float)
    percentChange = Column(Float)


class PropertyPriceSummary(Base):
    __tablename__ = "property_price_summary"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    state = Column(String(100))
    city = Column(String(100))
    locality = Column(String(200))
    Sale_resale = Column(String(50))
    transactionType = Column(String(50))
    period = Column(String(10))
    noOfTrans = Column(Integer)
    weightageAvgValue = Column(Float)
    compensationInCr = Column(Float)
    chargeableSQFT = Column('chargeableSQFTInMillion', Float)
    crdt = Column(DateTime)
