"""Setup script for the foundercap package."""
from setuptools import find_packages, setup

setup(
    name="foundercap",
    version="0.1.0",
    packages=find_packages(where="app"),
    package_dir={"": "app"},
    python_requires=">=3.9",
    install_requires=[
        "fastapi>=0.68.0,<0.69.0",
        "uvicorn[standard]>=0.15.0,<0.16.0",
        "pydantic>=1.8.0,<2.0.0",
        "python-dotenv>=0.19.0,<0.20.0",
        "sqlalchemy>=1.4.0,<2.0.0",
        "alembic>=1.7.0,<2.0.0",
        "psycopg2-binary>=2.9.0,<3.0.0",
        "redis>=4.0.0,<5.0.0",
        "python-jose[cryptography]>=3.3.0,<4.0.0",
        "passlib[bcrypt]>=1.7.4,<2.0.0",
        "python-multipart>=0.0.5,<0.6.0",
        "httpx>=0.22.0,<0.23.0",
        "aiohttp>=3.8.0,<4.0.0",
        "apscheduler>=3.9.0,<4.0.0",
        "aiosqlite>=0.17.0,<0.18.0",
        "email-validator>=1.1.3,<2.0.0",
        "pytz>=2021.3,<2023.0",
        "python-dateutil>=2.8.2,<3.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0,<8.0.0",
            "pytest-asyncio>=0.18.0,<0.19.0",
            "pytest-cov>=3.0.0,<4.0.0",
            "black>=22.0.0,<23.0.0",
            "isort>=5.10.0,<6.0.0",
            "mypy>=0.910,<1.0",
            "flake8>=4.0.0,<5.0.0",
            "mkdocs>=1.2.0,<2.0.0",
            "mkdocs-material>=8.0.0,<9.0.0",
            "mkdocstrings[python]>=0.18.0,<0.19.0",
            "pre-commit>=2.15.0,<3.0.0",
            "types-python-dateutil>=2.8.0,<3.0.0",
            "types-pytz>=2021.3.0,<2023.0.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "foundercap=foundercap.cli:main",
        ],
    },
)
