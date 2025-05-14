# 16 - Utilities Initialization

This file provides the pseudocode for the `__init__.py` file within the `app/utils/` directory. Its purpose is to make the utility functions and classes from the different utility modules easily importable from the `app.utils` package and to define the public interface of this package.

**Target Application File:** `app/utils/__init__.py`
**Corresponding Test File:** Typically, `__init__.py` files that only handle imports and `__all__` definitions don't have dedicated unit tests. The functionality of the utilities themselves is tested in their respective test files (e.g., `test_date_utils.py`).

## Pseudocode for Application Code (`app/utils/__init__.py`)

````python
"""
Utilities Initialization File (app/utils/__init__.py).

This file makes key utility functions and classes from the various utility
modules (date_utils, security_utils, accessibility_utils, formatters)
directly accessible under the `app.utils` package namespace.
This simplifies import statements in other parts of the application.
For example, instead of `from app.utils.date_utils import parse_date_range`,
one can use `from app.utils import parse_date_range`.

It also defines the `__all__` special variable, which specifies the public symbols
that are exported when a wildcard import (`from app.utils import *`) is used.
While explicit imports are generally preferred, `__all__` is good practice for
defining a clear public API for the package.
"""

import logging

# Import functions and classes from date_utils.py
from .date_utils import (
    parse_date_range,
    date_range_to_ga4_api_format,
    get_date_periods,
    format_date_for_display  # Renamed from format_date_pretty for consistency
)

# Import functions and classes from security_utils.py
from .security_utils import (
    generate_secure_token,
    generate_fernet_encryption_key, # Renamed from generate_encryption_key
    hash_password,
    verify_password,
    encrypt_data,
    decrypt_data,
    sanitize_input
)

# Import classes from accessibility_utils.py
from .accessibility_utils import AccessibilityChecker

# Import functions from formatters.py
from .formatters import (
    format_number,
    format_percentage,
    format_duration,
    format_date_pretty, # Keeping this distinct if its default format is preferred
    format_file_size
)

# Define __all__ to specify the public interface of the utils package.
# This list should include all the functions and classes intended to be
# directly importable from app.utils.
__all__ = [
    # From date_utils
    'parse_date_range',
    'date_range_to_ga4_api_format',
    'get_date_periods',
    'format_date_for_display',

    # From security_utils
    'generate_secure_token',
    'generate_fernet_encryption_key',
    'hash_password',
    'verify_password',
    'encrypt_data',
    'decrypt_data',
    'sanitize_input',

    # From accessibility_utils
    'AccessibilityChecker',

    # From formatters
    'format_number',
    'format_percentage',
    'format_duration',
    'format_date_pretty', # If this is kept distinct from format_date_for_display
    'format_file_size'
]

# Optional: Log that the utils package has been initialized.
logger = logging.getLogger(__name__)
logger.debug("app.utils package initialized. Exporting: %s", ", ".join(__all__))

Great! The screenshot confirms you have 15_Utility_Formatters.md.

We've completed the individual utility modules. The next step is to provide the __init__.py for the utils package.

Here is the content for 16_Utilities_Initialization.md:

File: 16_Utilities_Initialization.md
(You can copy everything below this line into a file named 16_Utilities_Initialization.md)

Markdown

# 16 - Utilities Initialization

This file provides the pseudocode for the `__init__.py` file within the `app/utils/` directory. Its purpose is to make the utility functions and classes from the different utility modules easily importable from the `app.utils` package and to define the public interface of this package.

**Target Application File:** `app/utils/__init__.py`
**Corresponding Test File:** Typically, `__init__.py` files that only handle imports and `__all__` definitions don't have dedicated unit tests. The functionality of the utilities themselves is tested in their respective test files (e.g., `test_date_utils.py`).

## Pseudocode for Application Code (`app/utils/__init__.py`)

```python
"""
Utilities Initialization File (app/utils/__init__.py).

This file makes key utility functions and classes from the various utility
modules (date_utils, security_utils, accessibility_utils, formatters)
directly accessible under the `app.utils` package namespace.
This simplifies import statements in other parts of the application.
For example, instead of `from app.utils.date_utils import parse_date_range`,
one can use `from app.utils import parse_date_range`.

It also defines the `__all__` special variable, which specifies the public symbols
that are exported when a wildcard import (`from app.utils import *`) is used.
While explicit imports are generally preferred, `__all__` is good practice for
defining a clear public API for the package.
"""

import logging

# Import functions and classes from date_utils.py
from .date_utils import (
    parse_date_range,
    date_range_to_ga4_api_format,
    get_date_periods,
    format_date_for_display  # Renamed from format_date_pretty for consistency
)

# Import functions and classes from security_utils.py
from .security_utils import (
    generate_secure_token,
    generate_fernet_encryption_key, # Renamed from generate_encryption_key
    hash_password,
    verify_password,
    encrypt_data,
    decrypt_data,
    sanitize_input
)

# Import classes from accessibility_utils.py
from .accessibility_utils import AccessibilityChecker

# Import functions from formatters.py
from .formatters import (
    format_number,
    format_percentage,
    format_duration,
    format_date_pretty, # Keeping this distinct if its default format is preferred
    format_file_size
)

# Define __all__ to specify the public interface of the utils package.
# This list should include all the functions and classes intended to be
# directly importable from app.utils.
__all__ = [
    # From date_utils
    'parse_date_range',
    'date_range_to_ga4_api_format',
    'get_date_periods',
    'format_date_for_display',

    # From security_utils
    'generate_secure_token',
    'generate_fernet_encryption_key',
    'hash_password',
    'verify_password',
    'encrypt_data',
    'decrypt_data',
    'sanitize_input',

    # From accessibility_utils
    'AccessibilityChecker',

    # From formatters
    'format_number',
    'format_percentage',
    'format_duration',
    'format_date_pretty', # If this is kept distinct from format_date_for_display
    'format_file_size'
]

# Optional: Log that the utils package has been initialized.
logger = logging.getLogger(__name__)
logger.debug("app.utils package initialized. Exporting: %s", ", ".join(__all__))



Note to LLM:
In utils-pseudocode.md, format_date was defined in formatters.py and format_date_for_display wasn't explicitly defined but date_utils.py had a format_date which was less feature-rich. formatters.py in 15_Utility_Formatters.md had format_date_pretty.
For clarity and to avoid name collision if both were to be imported from app.utils:

app.utils.date_utils.format_date_for_display is the more comprehensive one.
app.utils.formatters.format_date_pretty is kept if a specific "pretty" default is desired. The __all__ list reflects this by exporting format_date_for_display and format_date_pretty distinctly if they serve different primary purposes or have different default output formats. The original utils-pseudocode.md showed a format_date in its __all__ which was from formatters.py. I've aligned it to what we've been generating. The function generate_encryption_key in security_utils.py was more specifically generate_fernet_encryption_key, so that's reflected here.
````
