# #!/bin/bash

# # =============================================================================
# # Grant Lakebase Permissions to Databricks App Service Principal
# # =============================================================================
# # This script grants the necessary PostgreSQL permissions to a Databricks App's
# # service principal so it can read/write to the ai_chatbot schema and 
# # checkpoint tables in the public schema.
# #
# # Usage: ./grant-lakebase-permissions.sh
# #
# # The script will:
# # 1. Load configuration from .env.local if available
# # 2. Prompt for any missing required values
# # 3. Connect to Lakebase and execute GRANT statements
# # =============================================================================

# set -e

# # Colors for output
# RED='\033[0;31m'
# GREEN='\033[0;32m'
# YELLOW='\033[1;33m'
# BLUE='\033[0;34m'
# NC='\033[0m' # No Color

# # Print colored output
# print_info() {
#     echo -e "${BLUE}ℹ ${NC}$1"
# }

# print_success() {
#     echo -e "${GREEN}✓ ${NC}$1"
# }

# print_warning() {
#     echo -e "${YELLOW}⚠ ${NC}$1"
# }

# print_error() {
#     echo -e "${RED}✗ ${NC}$1"
# }

# print_step() {
#     echo -e "${BLUE}→ ${NC}$1"
# }

# # Banner
# echo ""
# echo "=============================================="
# echo "  Lakebase Permissions Grant Script"
# echo "=============================================="
# echo ""

# # Load environment variables from .env.local if it exists
# if [ -f ".env.local" ]; then
#     print_info "Loading environment variables from .env.local..."
#     export $(cat .env.local | grep -v '^#' | grep -v '^$' | xargs)
# fi

# # =============================================================================
# # Gather Required Configuration
# # =============================================================================

# # Lakebase connection string (PostgreSQL connection URL)
# # Format: postgresql://user:password@host:port/database
# if [ -z "$LAKEBASE_CONNECTION_STRING" ]; then
#     if [ -z "$DATABASE_URL" ]; then
#         echo ""
#         print_warning "No LAKEBASE_CONNECTION_STRING or DATABASE_URL found in environment."
#         echo ""
#         echo "Please enter your Lakebase PostgreSQL connection string."
#         echo "Format: postgresql://user:password@host:port/database"
#         echo ""
#         echo "You can find this in the Databricks UI:"
#         echo "  1. Go to your Lakebase instance"
#         echo "  2. Click 'Connection details'"
#         echo "  3. Copy the connection string"
#         echo ""
#         read -p "Connection string: " LAKEBASE_CONNECTION_STRING
#     else
#         LAKEBASE_CONNECTION_STRING="$DATABASE_URL"
#         print_info "Using DATABASE_URL from environment"
#     fi
# fi

# # App Service Principal Client ID
# # This is the UUID of the service principal associated with your Databricks App
# if [ -z "$APP_SERVICE_PRINCIPAL_ID" ]; then
#     echo ""
#     print_warning "No APP_SERVICE_PRINCIPAL_ID found in environment."
#     echo ""
#     echo "Please enter the Service Principal Client ID for your Databricks App."
#     echo ""
#     echo "You can find this in the Databricks UI:"
#     echo "  1. Go to your Databricks App"
#     echo "  2. Click on Authorization Tab"
#     echo "  3. Look for the 'Service Principal' under 'App authorization'"
#     echo "  4. Click the copy icon next to 'Service Principal' - value copied should be a UUID
#     echo ""
#     read -p "Service Principal Client ID: " APP_SERVICE_PRINCIPAL_ID
# fi

# # Validate inputs
# if [ -z "$LAKEBASE_CONNECTION_STRING" ]; then
#     print_error "Connection string is required."
#     exit 1
# fi

# if [ -z "$APP_SERVICE_PRINCIPAL_ID" ]; then
#     print_error "Service Principal Client ID is required."
#     exit 1
# fi

# # Validate UUID format (basic check)
# if ! [[ "$APP_SERVICE_PRINCIPAL_ID" =~ ^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$ ]]; then
#     print_warning "The Service Principal Client ID doesn't look like a valid UUID."
#     echo "Expected format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
#     read -p "Continue anyway? (y/N): " CONTINUE
#     if [[ ! "$CONTINUE" =~ ^[Yy]$ ]]; then
#         exit 1
#     fi
# fi

# echo ""
# print_info "Configuration:"
# echo "  Service Principal ID: $APP_SERVICE_PRINCIPAL_ID"
# echo "  Connection: [hidden for security]"
# echo ""

# # =============================================================================
# # Check for psql or Python
# # =============================================================================

# USE_PYTHON=false

# if command -v psql &> /dev/null; then
#     print_info "Using psql to connect to Lakebase..."
# elif command -v python3 &> /dev/null; then
#     print_warning "psql not found. Will use Python with psycopg2..."
#     USE_PYTHON=true
    
#     # Check if psycopg2 is available
#     if ! python3 -c "import psycopg2" 2>/dev/null; then
#         print_info "Installing psycopg2-binary..."
#         pip3 install psycopg2-binary --quiet --break-system-packages 2>/dev/null || \
#         pip3 install psycopg2-binary --quiet 2>/dev/null || \
#         pip install psycopg2-binary --quiet 2>/dev/null
        
#         if ! python3 -c "import psycopg2" 2>/dev/null; then
#             print_error "Failed to install psycopg2. Please install it manually:"
#             echo "  pip install psycopg2-binary"
#             exit 1
#         fi
#     fi
# else
#     print_error "Neither psql nor python3 found. Please install one of them."
#     exit 1
# fi

# # =============================================================================
# # SQL Statements to Execute
# # =============================================================================

# # Build the SQL statements
# SQL_STATEMENTS=$(cat <<EOF
# -- =============================================================================
# -- Grant permissions to Databricks App Service Principal
# -- Service Principal ID: ${APP_SERVICE_PRINCIPAL_ID}
# -- =============================================================================

# -- AI Chatbot Schema Permissions
# -- Granting USAGE on ai_chatbot schema
# GRANT USAGE ON SCHEMA ai_chatbot
# TO "${APP_SERVICE_PRINCIPAL_ID}";

# -- Granting SELECT, INSERT, UPDATE on all tables in ai_chatbot schema
# GRANT SELECT, INSERT, UPDATE
# ON ALL TABLES IN SCHEMA ai_chatbot
# TO "${APP_SERVICE_PRINCIPAL_ID}";

# -- Public Schema Permissions (for checkpoint tables)
# -- Granting USAGE on public schema
# GRANT USAGE ON SCHEMA public
# TO "${APP_SERVICE_PRINCIPAL_ID}";

# -- Granting permissions on checkpoint_migrations table
# GRANT SELECT, INSERT, UPDATE
# ON TABLE public.checkpoint_migrations
# TO "${APP_SERVICE_PRINCIPAL_ID}";

# -- Granting permissions on checkpoint_writes table
# GRANT SELECT, INSERT, UPDATE
# ON TABLE public.checkpoint_writes
# TO "${APP_SERVICE_PRINCIPAL_ID}";

# -- Granting permissions on checkpoints table
# GRANT SELECT, INSERT, UPDATE
# ON TABLE public.checkpoints
# TO "${APP_SERVICE_PRINCIPAL_ID}";

# -- Granting permissions on checkpoint_blobs table
# GRANT SELECT, INSERT, UPDATE
# ON TABLE public.checkpoint_blobs
# TO "${APP_SERVICE_PRINCIPAL_ID}";
# EOF
# )

# # =============================================================================
# # Execute SQL Statements
# # =============================================================================

# echo ""
# echo "=============================================="
# echo "  Executing SQL Grant Statements"
# echo "=============================================="
# echo ""

# if [ "$USE_PYTHON" = true ]; then
#     # Use Python with psycopg2
#     python3 << PYTHON_SCRIPT
# import psycopg2
# import sys

# connection_string = """${LAKEBASE_CONNECTION_STRING}"""
# sp_id = """${APP_SERVICE_PRINCIPAL_ID}"""

# # Individual SQL statements to execute
# statements = [
#     ("Granting USAGE permission on ai_chatbot schema", 
#      f'GRANT USAGE ON SCHEMA ai_chatbot TO "{sp_id}"'),
    
#     ("Granting SELECT, INSERT, UPDATE on all tables in ai_chatbot schema",
#      f'GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA ai_chatbot TO "{sp_id}"'),
    
#     ("Granting USAGE permission on public schema",
#      f'GRANT USAGE ON SCHEMA public TO "{sp_id}"'),
    
#     ("Granting permissions on checkpoint_migrations table",
#      f'GRANT SELECT, INSERT, UPDATE ON TABLE public.checkpoint_migrations TO "{sp_id}"'),
    
#     ("Granting permissions on checkpoint_writes table",
#      f'GRANT SELECT, INSERT, UPDATE ON TABLE public.checkpoint_writes TO "{sp_id}"'),
    
#     ("Granting permissions on checkpoints table",
#      f'GRANT SELECT, INSERT, UPDATE ON TABLE public.checkpoints TO "{sp_id}"'),
    
#     ("Granting permissions on checkpoint_blobs table",
#      f'GRANT SELECT, INSERT, UPDATE ON TABLE public.checkpoint_blobs TO "{sp_id}"'),
# ]

# try:
#     print("→ Connecting to Lakebase...")
#     conn = psycopg2.connect(connection_string)
#     conn.autocommit = True
#     cursor = conn.cursor()
#     print("✓ Connected successfully")
#     print("")
    
#     success_count = 0
#     error_count = 0
    
#     for description, sql in statements:
#         try:
#             print(f"→ {description}...")
#             cursor.execute(sql)
#             print(f"✓ {description} - Done")
#             success_count += 1
#         except psycopg2.Error as e:
#             error_msg = str(e).strip()
#             # Check if it's a "already granted" type of error (not critical)
#             if "already" in error_msg.lower() or "duplicate" in error_msg.lower():
#                 print(f"⚠ {description} - Already exists (skipped)")
#                 success_count += 1
#             else:
#                 print(f"✗ {description} - Error: {error_msg}")
#                 error_count += 1
    
#     cursor.close()
#     conn.close()
    
#     print("")
#     print("=" * 46)
#     print("  Summary")
#     print("=" * 46)
#     print(f"  Successful: {success_count}")
#     print(f"  Errors: {error_count}")
#     print("")
    
#     if error_count > 0:
#         print("⚠ Some permissions could not be granted.")
#         print("  This might be because:")
#         print("  - The schema or table doesn't exist yet")
#         print("  - You don't have permission to grant these privileges")
#         print("  - The service principal ID is incorrect")
#         sys.exit(1)
#     else:
#         print("✓ All permissions granted successfully!")
        
# except psycopg2.Error as e:
#     print(f"✗ Database connection error: {e}")
#     sys.exit(1)
# except Exception as e:
#     print(f"✗ Unexpected error: {e}")
#     sys.exit(1)
# PYTHON_SCRIPT

# else
#     # Use psql directly
    
#     # Create a temporary SQL file
#     TEMP_SQL_FILE=$(mktemp)
    
#     # Function to execute a single SQL statement with status output
#     execute_sql() {
#         local description="$1"
#         local sql="$2"
        
#         print_step "$description..."
        
#         if echo "$sql" | psql "$LAKEBASE_CONNECTION_STRING" 2>&1 | grep -qi "error\|denied"; then
#             print_error "$description - Failed"
#             return 1
#         else
#             print_success "$description - Done"
#             return 0
#         fi
#     }
    
#     print_step "Connecting to Lakebase..."
    
#     # Test connection
#     if ! psql "$LAKEBASE_CONNECTION_STRING" -c "SELECT 1" > /dev/null 2>&1; then
#         print_error "Failed to connect to Lakebase. Please check your connection string."
#         exit 1
#     fi
    
#     print_success "Connected successfully"
#     echo ""
    
#     SUCCESS_COUNT=0
#     ERROR_COUNT=0
    
#     # Execute each statement individually for better error reporting
    
#     # 1. ai_chatbot schema usage
#     execute_sql "Granting USAGE permission on ai_chatbot schema" \
#         "GRANT USAGE ON SCHEMA ai_chatbot TO \"${APP_SERVICE_PRINCIPAL_ID}\";" && \
#         ((SUCCESS_COUNT++)) || ((ERROR_COUNT++))
    
#     # 2. ai_chatbot tables
#     execute_sql "Granting SELECT, INSERT, UPDATE on all tables in ai_chatbot schema" \
#         "GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA ai_chatbot TO \"${APP_SERVICE_PRINCIPAL_ID}\";" && \
#         ((SUCCESS_COUNT++)) || ((ERROR_COUNT++))
    
#     # 3. public schema usage
#     execute_sql "Granting USAGE permission on public schema" \
#         "GRANT USAGE ON SCHEMA public TO \"${APP_SERVICE_PRINCIPAL_ID}\";" && \
#         ((SUCCESS_COUNT++)) || ((ERROR_COUNT++))
    
#     # 4. checkpoint_migrations
#     execute_sql "Granting permissions on checkpoint_migrations table" \
#         "GRANT SELECT, INSERT, UPDATE ON TABLE public.checkpoint_migrations TO \"${APP_SERVICE_PRINCIPAL_ID}\";" && \
#         ((SUCCESS_COUNT++)) || ((ERROR_COUNT++))
    
#     # 5. checkpoint_writes
#     execute_sql "Granting permissions on checkpoint_writes table" \
#         "GRANT SELECT, INSERT, UPDATE ON TABLE public.checkpoint_writes TO \"${APP_SERVICE_PRINCIPAL_ID}\";" && \
#         ((SUCCESS_COUNT++)) || ((ERROR_COUNT++))
    
#     # 6. checkpoints
#     execute_sql "Granting permissions on checkpoints table" \
#         "GRANT SELECT, INSERT, UPDATE ON TABLE public.checkpoints TO \"${APP_SERVICE_PRINCIPAL_ID}\";" && \
#         ((SUCCESS_COUNT++)) || ((ERROR_COUNT++))
    
#     # 7. checkpoint_blobs
#     execute_sql "Granting permissions on checkpoint_blobs table" \
#         "GRANT SELECT, INSERT, UPDATE ON TABLE public.checkpoint_blobs TO \"${APP_SERVICE_PRINCIPAL_ID}\";" && \
#         ((SUCCESS_COUNT++)) || ((ERROR_COUNT++))
    
#     echo ""
#     echo "=============================================="
#     echo "  Summary"
#     echo "=============================================="
#     echo "  Successful: $SUCCESS_COUNT"
#     echo "  Errors: $ERROR_COUNT"
#     echo ""
    
#     if [ $ERROR_COUNT -gt 0 ]; then
#         print_warning "Some permissions could not be granted."
#         echo "  This might be because:"
#         echo "  - The schema or table doesn't exist yet"
#         echo "  - You don't have permission to grant these privileges"
#         echo "  - The service principal ID is incorrect"
#         exit 1
#     else
#         print_success "All permissions granted successfully!"
#     fi
# fi

# echo ""
# echo "=============================================="
# echo "  Next Steps"
# echo "=============================================="
# echo ""
# echo "Your Databricks App service principal now has access to:"
# echo "  • ai_chatbot schema (USAGE, SELECT, INSERT, UPDATE on all tables)"
# echo "  • public.checkpoint_migrations (SELECT, INSERT, UPDATE)"
# echo "  • public.checkpoint_writes (SELECT, INSERT, UPDATE)"
# echo "  • public.checkpoints (SELECT, INSERT, UPDATE)"
# echo "  • public.checkpoint_blobs (SELECT, INSERT, UPDATE)"
# echo ""
# echo "You can now deploy and run your chatbot application!"
# echo ""
#!/bin/bash

# =============================================================================
# Grant Lakebase Permissions to Databricks App Service Principal
# =============================================================================
# This script grants the necessary PostgreSQL permissions to a Databricks App's
# service principal so it can read/write to the ai_chatbot schema and 
# checkpoint tables in the public schema.
#
# Usage: ./grant-lakebase-permissions.sh
#
# The script will:
# 1. Load configuration from .env.local if available
# 2. Prompt for any missing required values
# 3. Connect to Lakebase and execute GRANT statements
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_info() {
    echo -e "${BLUE}ℹ ${NC}$1"
}

print_success() {
    echo -e "${GREEN}✓ ${NC}$1"
}

print_warning() {
    echo -e "${YELLOW}⚠ ${NC}$1"
}

print_error() {
    echo -e "${RED}✗ ${NC}$1"
}

print_step() {
    echo -e "${BLUE}→ ${NC}$1"
}

# Banner
echo ""
echo "=============================================="
echo "  Lakebase Permissions Grant Script"
echo "=============================================="
echo ""

# Load environment variables from .env.local if it exists
if [ -f ".env.local" ]; then
    print_info "Loading environment variables from .env.local..."
    export $(cat .env.local | grep -v '^#' | grep -v '^$' | xargs)
fi

# =============================================================================
# Gather Required Configuration
# =============================================================================

# Lakebase connection string (PostgreSQL connection URL)
# Format: postgresql://user:password@host:port/database
if [ -z "$LAKEBASE_CONNECTION_STRING" ]; then
    if [ -z "$DATABASE_URL" ]; then
        echo ""
        print_warning "No LAKEBASE_CONNECTION_STRING or DATABASE_URL found in environment."
        echo ""
        echo "Please enter your Lakebase PostgreSQL connection string."
        echo "Format: postgresql://user:password@host:port/database"
        echo ""
        echo "You can find this in the Databricks UI:"
        echo "  1. Go to your Lakebase instance"
        echo "  2. Click 'Connection details'"
        echo "  3. Copy the connection string"
        echo ""
        read -p "Connection string: " LAKEBASE_CONNECTION_STRING
    else
        LAKEBASE_CONNECTION_STRING="$DATABASE_URL"
        print_info "Using DATABASE_URL from environment"
    fi
fi

# App Service Principal Client ID
# This is the UUID of the service principal associated with your Databricks App
if [ -z "$APP_SERVICE_PRINCIPAL_ID" ]; then
    echo ""
    print_warning "No APP_SERVICE_PRINCIPAL_ID found in environment."
    echo ""
    echo "Please enter the Service Principal Client ID for your Databricks App."
    echo ""
    echo "You can find this in the Databricks UI:"
    echo "  1. Go to your Databricks App"
    echo "  2. Click on Authorization Tab"
    echo "  3. Look for the 'Service Principal' under 'App authorization'"
    echo "  4. Click the copy icon next to 'Service Principal' - value copied should be a UUID
    echo ""
    read -p "Service Principal Client ID: " APP_SERVICE_PRINCIPAL_ID
fi

# Validate inputs
if [ -z "$LAKEBASE_CONNECTION_STRING" ]; then
    print_error "Connection string is required."
    exit 1
fi

if [ -z "$APP_SERVICE_PRINCIPAL_ID" ]; then
    print_error "Service Principal Client ID is required."
    exit 1
fi

# Validate UUID format (basic check)
if ! [[ "$APP_SERVICE_PRINCIPAL_ID" =~ ^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$ ]]; then
    print_warning "The Service Principal Client ID doesn't look like a valid UUID."
    echo "Expected format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
    read -p "Continue anyway? (y/N): " CONTINUE
    if [[ ! "$CONTINUE" =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
print_info "Configuration:"
echo "  Service Principal ID: $APP_SERVICE_PRINCIPAL_ID"
echo "  Connection: [hidden for security]"
echo ""

# =============================================================================
# Check for psql or Python
# =============================================================================

USE_PYTHON=false

if command -v psql &> /dev/null; then
    print_info "Using psql to connect to Lakebase..."
elif command -v python3 &> /dev/null; then
    print_warning "psql not found. Will use Python with psycopg2..."
    USE_PYTHON=true
    
    # Check if psycopg2 is available
    if ! python3 -c "import psycopg2" 2>/dev/null; then
        print_info "Installing psycopg2-binary..."
        pip3 install psycopg2-binary --quiet --break-system-packages 2>/dev/null || \
        pip3 install psycopg2-binary --quiet 2>/dev/null || \
        pip install psycopg2-binary --quiet 2>/dev/null
        
        if ! python3 -c "import psycopg2" 2>/dev/null; then
            print_error "Failed to install psycopg2. Please install it manually:"
            echo "  pip install psycopg2-binary"
            exit 1
        fi
    fi
else
    print_error "Neither psql nor python3 found. Please install one of them."
    exit 1
fi

# =============================================================================
# SQL Statements to Execute
# =============================================================================

# Build the SQL statements
SQL_STATEMENTS=$(cat <<EOF
-- =============================================================================
-- Grant permissions to Databricks App Service Principal
-- Service Principal ID: ${APP_SERVICE_PRINCIPAL_ID}
-- =============================================================================

-- AI Chatbot Schema Permissions
-- Granting USAGE on ai_chatbot schema
GRANT USAGE ON SCHEMA ai_chatbot
TO "${APP_SERVICE_PRINCIPAL_ID}";

-- Granting SELECT, INSERT, UPDATE on all tables in ai_chatbot schema
GRANT SELECT, INSERT, UPDATE
ON ALL TABLES IN SCHEMA ai_chatbot
TO "${APP_SERVICE_PRINCIPAL_ID}";

-- Public Schema Permissions (for checkpoint tables)
-- Granting USAGE on public schema
GRANT USAGE ON SCHEMA public
TO "${APP_SERVICE_PRINCIPAL_ID}";

-- Granting permissions on checkpoint_migrations table
GRANT SELECT, INSERT, UPDATE
ON TABLE public.checkpoint_migrations
TO "${APP_SERVICE_PRINCIPAL_ID}";

-- Granting permissions on checkpoint_writes table
GRANT SELECT, INSERT, UPDATE
ON TABLE public.checkpoint_writes
TO "${APP_SERVICE_PRINCIPAL_ID}";

-- Granting permissions on checkpoints table
GRANT SELECT, INSERT, UPDATE
ON TABLE public.checkpoints
TO "${APP_SERVICE_PRINCIPAL_ID}";

-- Granting permissions on checkpoint_blobs table
GRANT SELECT, INSERT, UPDATE
ON TABLE public.checkpoint_blobs
TO "${APP_SERVICE_PRINCIPAL_ID}";
EOF
)

# =============================================================================
# Execute SQL Statements
# =============================================================================

echo ""
echo "=============================================="
echo "  Executing SQL Grant Statements"
echo "=============================================="
echo ""

if [ "$USE_PYTHON" = true ]; then
    # Use Python with psycopg2
    python3 << PYTHON_SCRIPT
import psycopg2
import sys

connection_string = """${LAKEBASE_CONNECTION_STRING}"""
sp_id = """${APP_SERVICE_PRINCIPAL_ID}"""

# Individual SQL statements to execute
statements = [
    ("Granting USAGE permission on ai_chatbot schema", 
     f'GRANT USAGE ON SCHEMA ai_chatbot TO "{sp_id}"'),
    
    ("Granting SELECT, INSERT, UPDATE on all tables in ai_chatbot schema",
     f'GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA ai_chatbot TO "{sp_id}"'),
    
    ("Granting USAGE permission on public schema",
     f'GRANT USAGE ON SCHEMA public TO "{sp_id}"'),
    
    ("Granting permissions on checkpoint_migrations table",
     f'GRANT SELECT, INSERT, UPDATE ON TABLE public.checkpoint_migrations TO "{sp_id}"'),
    
    ("Granting permissions on checkpoint_writes table",
     f'GRANT SELECT, INSERT, UPDATE ON TABLE public.checkpoint_writes TO "{sp_id}"'),
    
    ("Granting permissions on checkpoints table",
     f'GRANT SELECT, INSERT, UPDATE ON TABLE public.checkpoints TO "{sp_id}"'),
    
    ("Granting permissions on checkpoint_blobs table",
     f'GRANT SELECT, INSERT, UPDATE ON TABLE public.checkpoint_blobs TO "{sp_id}"'),
]

try:
    print("→ Connecting to Lakebase...")
    conn = psycopg2.connect(connection_string)
    conn.autocommit = True
    cursor = conn.cursor()
    print("✓ Connected successfully")
    print("")
    
    success_count = 0
    error_count = 0
    
    for description, sql in statements:
        try:
            print(f"→ {description}...")
            cursor.execute(sql)
            print(f"✓ {description} - Done")
            success_count += 1
        except psycopg2.Error as e:
            error_msg = str(e).strip()
            # Check if it's a "already granted" type of error (not critical)
            if "already" in error_msg.lower() or "duplicate" in error_msg.lower():
                print(f"⚠ {description} - Already exists (skipped)")
                success_count += 1
            else:
                print(f"✗ {description} - Error: {error_msg}")
                error_count += 1
    
    cursor.close()
    conn.close()
    
    print("")
    print("=" * 46)
    print("  Summary")
    print("=" * 46)
    print(f"  Successful: {success_count}")
    print(f"  Errors: {error_count}")
    print("")
    
    if error_count > 0:
        print("⚠ Some permissions could not be granted.")
        print("  This might be because:")
        print("  - The schema or table doesn't exist yet")
        print("  - You don't have permission to grant these privileges")
        print("  - The service principal ID is incorrect")
        sys.exit(1)
    else:
        print("✓ All permissions granted successfully!")
        
except psycopg2.Error as e:
    print(f"✗ Database connection error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"✗ Unexpected error: {e}")
    sys.exit(1)
PYTHON_SCRIPT

else
    # Use psql directly
    
    # Create a temporary SQL file
    TEMP_SQL_FILE=$(mktemp)
    
    # Function to execute a single SQL statement with status output
    execute_sql() {
        local description="$1"
        local sql="$2"
        
        print_step "$description..."
        
        if echo "$sql" | psql "$LAKEBASE_CONNECTION_STRING" 2>&1 | grep -qi "error\|denied"; then
            print_error "$description - Failed"
            return 1
        else
            print_success "$description - Done"
            return 0
        fi
    }
    
    print_step "Connecting to Lakebase..."
    
    # Test connection
    if ! psql "$LAKEBASE_CONNECTION_STRING" -c "SELECT 1" > /dev/null 2>&1; then
        print_error "Failed to connect to Lakebase. Please check your connection string."
        exit 1
    fi
    
    print_success "Connected successfully"
    echo ""
    
    SUCCESS_COUNT=0
    ERROR_COUNT=0
    
    # Execute each statement individually for better error reporting
    
    # 1. ai_chatbot schema usage
    execute_sql "Granting USAGE permission on ai_chatbot schema" \
        "GRANT USAGE ON SCHEMA ai_chatbot TO \"${APP_SERVICE_PRINCIPAL_ID}\";" && \
        ((SUCCESS_COUNT++)) || ((ERROR_COUNT++))
    
    # 2. ai_chatbot tables
    execute_sql "Granting SELECT, INSERT, UPDATE on all tables in ai_chatbot schema" \
        "GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA ai_chatbot TO \"${APP_SERVICE_PRINCIPAL_ID}\";" && \
        ((SUCCESS_COUNT++)) || ((ERROR_COUNT++))
    
    # 3. public schema usage
    execute_sql "Granting USAGE permission on public schema" \
        "GRANT USAGE ON SCHEMA public TO \"${APP_SERVICE_PRINCIPAL_ID}\";" && \
        ((SUCCESS_COUNT++)) || ((ERROR_COUNT++))
    
    # 4. checkpoint_migrations
    execute_sql "Granting permissions on checkpoint_migrations table" \
        "GRANT SELECT, INSERT, UPDATE ON TABLE public.checkpoint_migrations TO \"${APP_SERVICE_PRINCIPAL_ID}\";" && \
        ((SUCCESS_COUNT++)) || ((ERROR_COUNT++))
    
    # 5. checkpoint_writes
    execute_sql "Granting permissions on checkpoint_writes table" \
        "GRANT SELECT, INSERT, UPDATE ON TABLE public.checkpoint_writes TO \"${APP_SERVICE_PRINCIPAL_ID}\";" && \
        ((SUCCESS_COUNT++)) || ((ERROR_COUNT++))
    
    # 6. checkpoints
    execute_sql "Granting permissions on checkpoints table" \
        "GRANT SELECT, INSERT, UPDATE ON TABLE public.checkpoints TO \"${APP_SERVICE_PRINCIPAL_ID}\";" && \
        ((SUCCESS_COUNT++)) || ((ERROR_COUNT++))
    
    # 7. checkpoint_blobs
    execute_sql "Granting permissions on checkpoint_blobs table" \
        "GRANT SELECT, INSERT, UPDATE ON TABLE public.checkpoint_blobs TO \"${APP_SERVICE_PRINCIPAL_ID}\";" && \
        ((SUCCESS_COUNT++)) || ((ERROR_COUNT++))
    
    echo ""
    echo "=============================================="
    echo "  Summary"
    echo "=============================================="
    echo "  Successful: $SUCCESS_COUNT"
    echo "  Errors: $ERROR_COUNT"
    echo ""
    
    if [ $ERROR_COUNT -gt 0 ]; then
        print_warning "Some permissions could not be granted."
        echo "  This might be because:"
        echo "  - The schema or table doesn't exist yet"
        echo "  - You don't have permission to grant these privileges"
        echo "  - The service principal ID is incorrect"
        exit 1
    else
        print_success "All permissions granted successfully!"
    fi
fi

echo ""
echo "=============================================="
echo "  Next Steps"
echo "=============================================="
echo ""
echo "Your Databricks App service principal now has access to:"
echo "  • ai_chatbot schema (USAGE, SELECT, INSERT, UPDATE on all tables)"
echo "  • public.checkpoint_migrations (SELECT, INSERT, UPDATE)"
echo "  • public.checkpoint_writes (SELECT, INSERT, UPDATE)"
echo "  • public.checkpoints (SELECT, INSERT, UPDATE)"
echo "  • public.checkpoint_blobs (SELECT, INSERT, UPDATE)"
echo ""
echo "You can now deploy and run your chatbot application!"
echo ""