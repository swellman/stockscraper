from sqlalchemy import create_engine, Column, Integer, String, Float, Date, ForeignKey, Sequence
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class Stock(Base):
    __tablename__ = 'stocks'
    id = Column(Integer, Sequence('stock_id_seq'), primary_key=True)
    symbol = Column(String(10), unique=True, nullable=False)
    name = Column(String(50))

class HistoricalData(Base):
    __tablename__ = 'historical_data'
    id = Column(Integer, Sequence('historical_data_id_seq'), primary_key=True)
    stock_id = Column(Integer, ForeignKey('stocks.id'))
    date = Column(Date)
    close = Column(Float)
    stock = relationship("Stock", back_populates="historical_data")

Stock.historical_data = relationship("HistoricalData", order_by=HistoricalData.date, back_populates="stock")
