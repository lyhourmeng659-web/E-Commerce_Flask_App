from app.core.base_service import BaseService
from app.core.extensions import db
from app.modules.categories.model import Category
from .schema import CategorySchema
from .utils import generate_slug, normalize_name
from app.shared.constants import DEFAULT_PAGE, DEFAULT_PER_PAGE

# Schema instances reused across all service calls (more efficient than
# instantiating inside each method)
category_schema = CategorySchema()
categories_schema = CategorySchema(many=True)


class CategoryService(BaseService):
    """
    Service layer for all Category business logic.
    Inherits get_by_id, get_all, save, count etc. from BaseService.
    Overrides only methods that need category-specific logic.
    """
    model = Category

    @staticmethod
    def get_paginated(page: int = DEFAULT_PAGE, per_page: int = DEFAULT_PER_PAGE):
        """
        Return paginated categories sorted alphabetically by name.
        Used on the public categories list page.
        """
        return (
            Category.query
            .order_by(Category.name.asc())
            .paginate(page=page, per_page=per_page, error_out=False)
        )

    @staticmethod
    def get_all_nav():
        """
        Return all categories for the navigation dropdown.
        Fetches only id, name, slug — no products loaded.
        Called on every page via context processor in create_app().
        """
        return Category.query.order_by(Category.name.asc()).all()

    @staticmethod
    def get_by_slug(slug: str):
        """
        Fetch a single category by its URL slug.
        Returns None if not found — caller handles 404.
        Use indexed column for fast lookup.
        """
        return Category.query.filter_by(slug=slug).first()

    @staticmethod
    def get_paginated_products(category: Category, page: int = DEFAULT_PAGE, per_page: int = DEFAULT_PER_PAGE):
        """
        Return paginated products belonging to a category.
        Keeps product listing consistent with the rest of the app
        and prevents loading hundreds of products at once.
        """
        from app.modules.products.model import Product
        return (
            Product.query
            .filter_by(category_id=category.id)
            .order_by(Product.id.desc())
            .paginate(page=page, per_page=per_page, error_out=False)
        )

    @staticmethod
    def create(data: dict) -> Category:
        """
        Validate and create a new category.

        Process:
        1. Validate input via Marshmallow schema (strips whitespace, checks length)
        2. Normalize name to Title Case
        3. Auto-generate slug from name if not provided
        4. Check for duplicate name and slug
        5. Persist and return the Category model object

        Returns the Category model (not a dict) so routes can use it directly.
        Raises ValueError for validation/duplicate errors caught in routes.
        """
        validated = category_schema.load(data)

        name = normalize_name(validated["name"])
        slug = generate_slug(validated.get("slug") or name)

        if Category.query.filter_by(name=name).first():
            raise ValueError("A category with this name already exists.")

        if Category.query.filter_by(slug=slug).first():
            raise ValueError("A category with this slug already exists.")

        category = Category(
            name=name,
            slug=slug,
            description=validated.get("description"),
        )
        db.session.add(category)
        db.session.commit()
        return category

    @staticmethod
    def update(category_id: int, data: dict) -> Category:
        """
        Validate and update an existing category.

        Checks for duplicate name/slug excluding the current record
        (allows keeping the same name without triggering a conflict).
        Returns the updated Category model object.
        Raises ValueError if not found or duplicates exist.
        """
        category = db.session.get(Category, category_id)
        if not category:
            raise ValueError("Category not found.")

        validated = category_schema.load(data)
        name = normalize_name(validated["name"])
        slug = generate_slug(validated.get("slug") or name)

        # Check for name conflict — exclude current category from check
        if Category.query.filter(
                Category.name == name,
                Category.id != category_id
        ).first():
            raise ValueError("A category with this name already exists.")

        # Check for slug conflict — exclude current category from check
        if Category.query.filter(
                Category.slug == slug,
                Category.id != category_id
        ).first():
            raise ValueError("A category with this slug already exists.")

        category.name = name
        category.slug = slug
        category.description = validated.get("description", category.description)

        db.session.commit()
        return category

    @staticmethod
    def delete(category_id: int) -> None:
        """
        Delete a category by ID.
        Due to cascade="all, delete" on the relationship,
        all products belonging to this category are also deleted.
        Raises ValueError if category not found.
        """
        category = db.session.get(Category, category_id)
        if not category:
            raise ValueError("Category not found.")
        db.session.delete(category)
        db.session.commit()
