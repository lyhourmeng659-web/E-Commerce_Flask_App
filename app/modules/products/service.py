from app.core.base_service import BaseService
from app.core.extensions import db
from app.modules.categories.model import Category
from app.modules.products.model import Product
from sqlalchemy import or_
from app.shared.helpers import generate_slug
from app.shared.constants import DEFAULT_PAGE, DEFAULT_PER_PAGE, LOW_STOCK_THRESHOLD
from .schema import ProductSchema
from .utils import save_product_image

product_schema = ProductSchema()


class ProductService(BaseService):
    """
    Service layer for all Product business logic.
    Inherits get_by_id, get_all, count, save from BaseService.
    """
    model = Product

    @staticmethod
    def get_paginated(page: int = DEFAULT_PAGE, per_page: int = DEFAULT_PER_PAGE):
        """
        Return paginated in-stock products, newest first.
        Filters out out-of-stock products for public listing.
        """
        return (
            Product.query
            .filter(Product.stock > 0)
            .order_by(Product.created_at.desc())
            .paginate(page=page, per_page=per_page, error_out=False)
        )

    @staticmethod
    def get_featured(limit: int = 8):
        """
        Return a flat list of newest in-stock products for the home page.
        Not paginated — home page shows a fixed number of featured items.
        Used by main routes to pass `products` to product_featured.html partial.
        """
        return (
            Product.query
            .filter(Product.stock > 0)
            .order_by(Product.created_at.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def search(keyword: str, page: int = DEFAULT_PAGE, per_page: int = DEFAULT_PER_PAGE):
        """
        Full-text search across product title, slug, description, and category name.

        Uses ilike for case-insensitive matching.
        Join Category so we can search by category name too.
        Only returns in-stock products.
        """
        return (
            Product.query
            .join(Category)
            .filter(
                Product.stock > 0,
                or_(
                    Product.title.ilike(f"%{keyword}%"),
                    Product.slug.ilike(f"%{keyword}%"),
                    Product.description.ilike(f"%{keyword}%"),
                    Category.name.ilike(f"%{keyword}%"),
                )
            )
            .order_by(Product.created_at.desc())
            .paginate(page=page, per_page=per_page, error_out=False)
        )

    @staticmethod
    def create(data: dict, image_file) -> Product:
        """
        Validate and create a new product.

        Process:
        1. Validate input with ProductSchema (type coercion + field validation)
        2. Auto-generate slug from title
        3. Check for duplicate title and slug
        4. Verify category exists
        5. Save image and persist product

        Returns the Product model object (not a dict) for use in routes.
        Raises ValueError for all business rule violations.
        """
        validated = product_schema.load(data)

        title = validated["title"]
        slug = generate_slug(title)

        if Product.query.filter_by(title=title).first():
            raise ValueError("A product with this title already exists.")

        if Product.query.filter_by(slug=slug).first():
            raise ValueError("A product with this slug already exists.")

        category = db.session.get(Category, validated["category_id"])
        if not category:
            raise ValueError("Selected category does not exist.")

        image_path = save_product_image(image_file)

        product = Product(
            title=title,
            slug=slug,
            description=validated.get("description"),
            price=validated["price"],
            stock=validated["stock"],
            category_id=validated["category_id"],
            image=image_path,
        )

        db.session.add(product)
        db.session.commit()
        return product

    @staticmethod
    def update(product_id: int, data: dict, image_file=None) -> Product:
        """
        Validate and update an existing product.

        Only update the image if a new file is provided.
        Checks for duplicate title/slug excluding the current product.
        Returns the updated Product model object.
        """
        product = db.session.get(Product, product_id)
        if not product:
            raise ValueError("Product not found.")

        validated = product_schema.load(data)
        title = validated["title"]
        slug = generate_slug(title)

        # Check conflicts excluding the current product
        if Product.query.filter(
                Product.title == title,
                Product.id != product_id
        ).first():
            raise ValueError("A product with this title already exists.")

        if Product.query.filter(
                Product.slug == slug,
                Product.id != product_id
        ).first():
            raise ValueError("A product with this slug already exists.")

        category = db.session.get(Category, validated["category_id"])
        if not category:
            raise ValueError("Selected category does not exist.")

        product.title = title
        product.slug = slug
        product.description = validated.get("description", product.description)
        product.price = validated["price"]
        product.stock = validated["stock"]
        product.category_id = validated["category_id"]

        # Only update the image if a new file was actually uploaded
        if image_file and image_file.filename:
            product.image = save_product_image(image_file)

        db.session.commit()
        return product

    @staticmethod
    def delete(product_id: int) -> None:
        """
        Delete a product by ID.
        Raises ValueError if product is not found.
        """
        product = db.session.get(Product, product_id)
        if not product:
            raise ValueError("Product not found.")
        db.session.delete(product)
        db.session.commit()

    @staticmethod
    def get_low_stock_products():
        """
        Return all products with stock below the LOW_STOCK_THRESHOLD.
        Ordered by stock ascending so most critical items appear first.
        Used in admin dashboard to trigger restocking alerts.
        """
        return (
            Product.query
            .filter(Product.stock < LOW_STOCK_THRESHOLD)
            .order_by(Product.stock.asc())
            .all()
        )
