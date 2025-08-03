from typing import Generic, TypeVar, List, Optional, Type
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
import math

T = TypeVar('T', bound=BaseModel)


class PaginationParams(BaseModel):
    """Pagination parameters for list endpoints - purely about pagination mechanics"""
    page: int = Field(default=1, ge=1, description="Page number (starts from 1)")
    size: int = Field(default=20, ge=1, le=100, description="Number of results per page")

    class Config:
        json_schema_extra = {
            "example": {
                "page": 1,
                "size": 20
            }
        }


class PaginationMeta(BaseModel):
    """Pagination metadata"""
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Number of results per page")
    total: int = Field(..., description="Total number of results")
    pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_prev: bool = Field(..., description="Whether there is a previous page")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response"""
    results: List[T] = Field(..., description="List of results")
    meta: PaginationMeta = Field(..., description="Pagination metadata")


class PaginationHandler:
    """Global pagination handler utility class"""
    
    @staticmethod
    def create_meta(page: int, size: int, total: int) -> PaginationMeta:
        """
        Create pagination metadata
        
        Args:
            page: Current page number
            size: results per page
            total: Total number of results
            
        Returns:
            PaginationMeta object
        """
        total_pages = math.ceil(total / size) if total > 0 else 0
        has_next = page < total_pages
        has_prev = page > 1
        
        return PaginationMeta(
            page=page,
            size=size,
            total=total,
            pages=total_pages,
            has_next=has_next,
            has_prev=has_prev
        )
    
    @staticmethod
    async def paginate_query(
        db: AsyncSession,
        query,
        pagination: PaginationParams,
        response_schema: Type[T]
    ) -> PaginatedResponse[T]:
        """
        Complete pagination handling - takes a query and returns paginated response
        
        Args:
            db: Database session
            query: SQLAlchemy query object (with filters already applied)
            pagination: Pagination parameters
            response_schema: Pydantic schema class for response results
            
        Returns:
            PaginatedResponse with results converted to response_schema
        """
        # Get total count
        # Extract the main table for counting
        count_query = select(func.count()).select_from(query.froms[0])
        
        # Apply the same where conditions if they exist
        if query.whereclause is not None:
            count_query = count_query.where(query.whereclause)
            
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Apply pagination to the original query
        offset = (pagination.page - 1) * pagination.size
        paginated_query = query.offset(offset).limit(pagination.size)
        
        # Execute paginated query
        result = await db.execute(paginated_query)
        # Use unique() to handle joined eager loads with collections
        results = list(result.unique().scalars().all())
        
        # Convert results to response schema
        response_results = [response_schema.model_validate(item) for item in results]
        
        # Create pagination metadata
        meta = PaginationHandler.create_meta(pagination.page, pagination.size, total)
        
        # Return paginated response
        return PaginatedResponse(results=response_results, meta=meta)
    
    @staticmethod
    def apply_pagination(query, page: int, size: int):
        """
        Apply pagination to a query (legacy method - prefer paginate_query)
        
        Args:
            query: SQLAlchemy query
            page: Page number
            size: results per page
            
        Returns:
            Query with pagination applied
        """
        offset = (page - 1) * size
        return query.offset(offset).limit(size)
    
    @staticmethod
    def create_response(results: List[T], meta: PaginationMeta) -> PaginatedResponse[T]:
        """
        Create a paginated response (legacy method - prefer paginate_query)
        
        Args:
            results: List of results
            meta: Pagination metadata
            
        Returns:
            PaginatedResponse object
        """
        return PaginatedResponse(results=results, meta=meta) 