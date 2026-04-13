from app.core.extensions import db
from app.shared.constants import DEFAULT_PAGE, DEFAULT_PER_PAGE


class BaseService:
    """
    Base service class providing reusable CRUD and query operations.

    Usage:
        class ProductService(BaseService):
            model = Product

    Every child service inherits these methods automatically,
    avoiding repetition across all module services.
    """

    model = None  # Must be overridden in each child service class

    # Read Operations

    @classmethod
    def get_by_id(cls, record_id: int):
        """
        Fetch a single record by its primary key.
        Returns None if not found (does not raise 404).
        Use this when you want to handle missing records manually.
        """
        return cls.model.query.get(record_id)

    @classmethod
    def get_by_id_or_404(cls, record_id: int):
        """
        Fetch a single record by primary key or abort with HTTP 404.
        Use this in route handlers where missing = page not found.
        """
        return cls.model.query.get_or_404(record_id)

    @classmethod
    def get_all(cls):
        """
        Fetch all records for this model, ordered by primary key descending.
        Returns newest records first by default.
        """
        return cls.model.query.order_by(cls.model.id.desc()).all()

    @classmethod
    def paginate(cls, page: int = DEFAULT_PAGE, per_page: int = DEFAULT_PER_PAGE):
        """
        Paginate all records, ordered by newest first.

        Args:
            page: Current page number (1-indexed)
            per_page: Number of records per page

        Returns:
            Flask-SQLAlchemy Pagination object with:
            - .items        → list of records on current page
            - .total        → total record count
            - .pages        → total page count
            - .has_next     → bool, whether next page exists
            - .has_prev     → bool, whether prev page exists
            - .next_num     → next page number
            - .prev_num     → previous page number

        error_out=False means invalid page numbers return empty
        results instead of raising a 404.
        """
        return (
            cls.model.query
            .order_by(cls.model.id.desc())
            .paginate(page=page, per_page=per_page, error_out=False)
        )

    @classmethod
    def count(cls) -> int:
        """
        Return the total number of records for this model.
        More efficient than len(get_all()) as it uses SQL COUNT.
        """
        return cls.model.query.count()

    # Write Operations

    @classmethod
    def create(cls, **kwargs):
        """
        Create and persist a new record.

        Usage:
            ProductService.create(name="GPU", price=499.99)

        Passes all keyword arguments directly to the model constructor,
        then commits to the database.
        Returns the newly created record.
        """
        record = cls.model(**kwargs)
        db.session.add(record)
        db.session.commit()
        return record

    @classmethod
    def update(cls, record_id: int, **kwargs):
        """
        Update an existing record by ID.

        Usage:
            ProductService.update(5, price=399.99, name="New Name")

        Uses setattr() to dynamically update only the provided fields.
        Returns the updated record, or None if not found.
        """
        record = cls.get_by_id(record_id)
        if not record:
            return None
        for key, value in kwargs.items():
            setattr(record, key, value)
        db.session.commit()
        return record

    @classmethod
    def delete(cls, record_id: int) -> bool:
        """
        Delete a record by ID.

        Returns True if deleted successfully, False if record not found.
        Rolls back the session if deletion fails unexpectedly.
        """
        record = cls.get_by_id(record_id)
        if not record:
            return False
        db.session.delete(record)
        db.session.commit()
        return True

    @classmethod
    def save(cls, record):
        """
        Persist an already-instantiated model object.

        Usage:
            product = Product(name="GPU")
            ProductService.save(product)

        Useful when you need to manipulate the object before saving,
        rather than passing kwargs to create().
        """
        db.session.add(record)
        db.session.commit()
        return record
