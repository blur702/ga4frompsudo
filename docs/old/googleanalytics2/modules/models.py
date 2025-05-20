from datetime import datetime
import json
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, Float, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

db = SQLAlchemy()

class Property(db.Model):
    """
    Stores information about Google Analytics 4 properties.
    """
    __tablename__ = 'property'
    
    id = Column(Integer, primary_key=True)
    ga_property_id = Column(String(80), nullable=False, unique=True)
    display_name = Column(String(120), nullable=False)
    website_url = Column(String(255), nullable=True)
    exclude_from_global_reports = Column(Boolean, nullable=False, default=False)
    last_synced = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    analytics_data = relationship("AnalyticsData", back_populates="property", cascade="all, delete-orphan")
    structured_metrics = relationship("StructuredMetric", back_populates="property", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Property {self.display_name}>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'ga_property_id': self.ga_property_id,
            'display_name': self.display_name,
            'website_url': self.website_url,
            'exclude_from_global_reports': self.exclude_from_global_reports,
            'last_synced': self.last_synced.isoformat() if self.last_synced else None
        }


class AnalyticsData(db.Model):
    """
    Stores raw analytics data fetched from Google Analytics.
    """
    __tablename__ = 'analytics_data'
    
    id = Column(Integer, primary_key=True)
    property_id = Column(Integer, ForeignKey('property.id'), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    report_start_date = Column(Date, nullable=False)
    report_end_date = Column(Date, nullable=False)
    raw_data_json = Column(Text, nullable=True)
    
    # Relationships
    property = relationship("Property", back_populates="analytics_data")
    structured_metrics = relationship("StructuredMetric", back_populates="analytics_data", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<AnalyticsData {self.property_id} {self.report_start_date} to {self.report_end_date}>"
    
    def get_raw_data(self):
        """
        Returns the raw data as a Python dictionary.
        """
        if self.raw_data_json:
            return json.loads(self.raw_data_json)
        return None


class Setting(db.Model):
    """
    Stores application settings as key-value pairs.
    Some settings (like API keys) are stored encrypted.
    """
    __tablename__ = 'setting'
    
    id = Column(Integer, primary_key=True)
    key = Column(String(50), nullable=False, unique=True)
    value = Column(Text, nullable=True)
    description = Column(String(255), nullable=True)
    is_encrypted = Column(Boolean, default=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Setting {self.key}>"
    
    @classmethod
    def get_value(cls, key, default=None):
        """
        Get a setting value by key.
        
        Args:
            key (str): The setting key.
            default: The default value to return if the setting doesn't exist.
            
        Returns:
            The setting value, or the default if not found.
        """
        from flask import current_app
        
        setting = cls.query.filter_by(key=key).first()
        if not setting:
            return default
            
        # If the setting is encrypted, decrypt it
        if setting.is_encrypted:
            from modules.encryption import decrypt_value
            return decrypt_value(setting.value)
            
        return setting.value
    
    @classmethod
    def set_value(cls, key, value, description=None, is_encrypted=False):
        """
        Set a setting value.
        
        Args:
            key (str): The setting key.
            value: The setting value.
            description (str, optional): A description of the setting.
            is_encrypted (bool): Whether to encrypt the value.
            
        Returns:
            Setting: The setting object.
        """
        from flask import current_app
        
        # If value is None, don't proceed
        if value is None:
            return None
            
        # Encrypt the value if needed
        if is_encrypted:
            from modules.encryption import encrypt_value
            encrypted_value = encrypt_value(value)
            if encrypted_value is None:
                return None
            value = encrypted_value
        
        setting = cls.query.filter_by(key=key).first()
        if setting:
            # Only update if the value has changed
            if setting.value != value:
                setting.value = value
                setting.is_encrypted = is_encrypted
                if description:
                    setting.description = description
        else:
            setting = cls(
                key=key,
                value=value,
                description=description,
                is_encrypted=is_encrypted
            )
            db.session.add(setting)
        
        db.session.commit()
        return setting


class PropertySelectionSet(db.Model):
    """
    Allows users to save and reuse selections of properties for generating reports.
    """
    __tablename__ = 'property_selection_set'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(String(255), nullable=True)
    property_ids = Column(Text, nullable=False)  # JSON list of Property.id values
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<PropertySelectionSet {self.name}>"
    
    def get_property_ids(self):
        """
        Returns the property IDs as a Python list.
        """
        return json.loads(self.property_ids)
    
    def set_property_ids(self, ids):
        """
        Sets the property IDs from a Python list.
        """
        self.property_ids = json.dumps(ids)


class ReportTemplate(db.Model):
    """
    Allows users to save and reuse report templates with specific metrics, dimensions, and URL configurations.
    """
    __tablename__ = 'report_template'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    metrics = Column(Text, nullable=False)  # JSON list of selected metric names
    dimensions = Column(Text, nullable=False)  # JSON list of selected dimension names
    url_type = Column(String(20), nullable=False)  # 'single' or 'multiple'
    saved_urls = Column(Text, nullable=True)  # JSON list of saved URLs
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<ReportTemplate {self.name}>"
    
    def get_metrics(self):
        """
        Returns the metrics as a Python list.
        """
        return json.loads(self.metrics)
    
    def set_metrics(self, metrics_list):
        """
        Sets the metrics from a Python list.
        """
        self.metrics = json.dumps(metrics_list)
    
    def get_dimensions(self):
        """
        Returns the dimensions as a Python list.
        """
        return json.loads(self.dimensions)
    
    def set_dimensions(self, dimensions_list):
        """
        Sets the dimensions from a Python list.
        """
        self.dimensions = json.dumps(dimensions_list)
    
    def get_saved_urls(self):
        """
        Returns the saved URLs as a Python list.
        """
        if self.saved_urls:
            return json.loads(self.saved_urls)
        return []
    
    def set_saved_urls(self, urls_list):
        """
        Sets the saved URLs from a Python list.
        """
        self.saved_urls = json.dumps(urls_list)


class MetricDefinition(db.Model):
    """
    Stores metadata about GA4 metrics.
    """
    __tablename__ = 'metric_definition'
    
    id = Column(Integer, primary_key=True)
    api_name = Column(String(100), nullable=False, unique=True)
    display_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=True)
    aggregation_type = Column(String(20), nullable=False, default="sum")
    is_custom = Column(Boolean, nullable=False, default=False)
    is_deprecated = Column(Boolean, nullable=False, default=False)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    structured_metrics = relationship("StructuredMetric", back_populates="metric_definition")
    
    def __repr__(self):
        return f"<MetricDefinition {self.api_name}>"


class DimensionDefinition(db.Model):
    """
    Stores metadata about GA4 dimensions.
    """
    __tablename__ = 'dimension_definition'
    
    id = Column(Integer, primary_key=True)
    api_name = Column(String(100), nullable=False, unique=True)
    display_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=True)
    is_custom = Column(Boolean, nullable=False, default=False)
    is_deprecated = Column(Boolean, nullable=False, default=False)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    dimension_values = relationship("DimensionValue", back_populates="dimension_definition", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<DimensionDefinition {self.api_name}>"


class DimensionValue(db.Model):
    """
    Stores common dimension values for better display and filtering.
    """
    __tablename__ = 'dimension_value'
    
    id = Column(Integer, primary_key=True)
    dimension_id = Column(Integer, ForeignKey('dimension_definition.id'), nullable=False)
    api_value = Column(String(255), nullable=False)
    display_value = Column(String(255), nullable=False)
    
    # Relationships
    dimension_definition = relationship("DimensionDefinition", back_populates="dimension_values")
    
    def __repr__(self):
        return f"<DimensionValue {self.dimension_definition.api_name}:{self.api_value}>"


class StructuredMetric(db.Model):
    """
    Stores structured metrics data extracted from the raw GA4 API response.
    """
    __tablename__ = 'structured_metric'
    
    id = Column(Integer, primary_key=True)
    analytics_data_id = Column(Integer, ForeignKey('analytics_data.id'), nullable=False)
    property_id = Column(Integer, ForeignKey('property.id'), nullable=False, index=True)
    metric_id = Column(Integer, ForeignKey('metric_definition.id'), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    value = Column(Float, nullable=False)
    dimensions_json = Column(Text, nullable=True)  # JSON string of dimension key-value pairs
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    analytics_data = relationship("AnalyticsData", back_populates="structured_metrics")
    property = relationship("Property", back_populates="structured_metrics")
    metric_definition = relationship("MetricDefinition", back_populates="structured_metrics")
    
    def __repr__(self):
        return f"<StructuredMetric {self.metric_definition.api_name} for {self.date}>"
    
    def get_dimensions(self):
        """
        Returns the dimensions as a Python dictionary.
        """
        if self.dimensions_json:
            return json.loads(self.dimensions_json)
        return {}
    
    def set_dimensions(self, dimensions_dict):
        """
        Sets the dimensions from a Python dictionary.
        """
        self.dimensions_json = json.dumps(dimensions_dict)