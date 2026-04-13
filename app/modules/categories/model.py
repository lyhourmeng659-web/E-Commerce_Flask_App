from datetime import datetime, timezone
from app.core.extensions import db


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(120), nullable=False, unique=True)

    # Indexed for fast slug-based lookups in category_detail route
    slug = db.Column(db.String(120), nullable=False, unique=True, index=True)

    # Optional description for SEO meta tags and category header text
    description = db.Column(db.Text, nullable=True)

    # timezone.utc is the modern replacement for deprecated utcnow() in Python 3.12+
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationship to products:
    # - back_populates: mirrors Product.category relationship
    # - cascade="all, delete": deleting a category deletes its products
    # - passive_deletes=True: lets the DB handle cascade (more efficient)
    # - lazy="select": loads products only when accessed, not on every category query
    #   (from "select" to avoid loading products on list pages)
    products = db.relationship(
        "Product",
        back_populates="category",
        cascade="all, delete",
        passive_deletes=True,
        lazy="select",
    )

    def __repr__(self):
        return f"<Category {self.name}>"

    @property
    def product_count(self):
        """
        Returns the count of products using SQL COUNT — efficient because
        it runs a single COUNT query instead of loading all product rows
        into Python memory just to call len() on them.
        """
        from app.core.extensions import db
        from sqlalchemy import func
        from app.modules.products.model import Product
        return db.session.query(func.count(Product.id)) \
            .filter(Product.category_id == self.id) \
            .scalar()
